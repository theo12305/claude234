"""One input field on the page: number, toggle and drop-down fields with their typical range, the drop-downs that
fill in typical values, the monthly table, the shapefile upload and the hourly demand file. And the input drawings
beside the fields."""
from __future__ import annotations

import hashlib
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ghe_web import i18n
from ghe_web.charts import input_drawings
from ghe_web.core import geometry, hourly, model
from ghe_web.i18n import fmt, t
from ghe_web.inputs import Property, Variant
from ghe_web.page import guidance, look


def widget(prop: Property, value, key: str):
    label = f"{t(prop.label)} [{t(prop.unit)}]" if prop.unit else t(prop.label)
    help_text = t(prop.help) or None
    # A preset may already have put a value in the session state; then the widget must not get one too.
    initial = {} if key in st.session_state else None
    if prop.kind == "float":
        kw = initial if initial is not None else {"value": float(value)}
        as_float = lambda x: float(x) if x is not None else None  # noqa: E731 (Streamlit refuses mixed int/float)
        return st.number_input(label, min_value=as_float(prop.min), max_value=as_float(prop.max),
                               step=as_float(prop.step), format=prop.format, help=help_text, key=key, **kw)
    if prop.kind == "int":
        kw = initial if initial is not None else {"value": int(value)}
        return int(st.number_input(label, min_value=int(prop.min) if prop.min is not None else None,
                                   max_value=int(prop.max) if prop.max is not None else None,
                                   step=int(prop.step or 1), help=help_text, key=key, **kw))
    if prop.kind == "bool":
        kw = initial if initial is not None else {"value": bool(value)}
        return st.toggle(label, help=help_text, key=key, **kw)
    if prop.kind == "choice":
        kw = initial if initial is not None else {"index": prop.options.index(value)}
        return st.selectbox(label, prop.options, format_func=t, help=help_text, key=key, **kw)
    raise ValueError(prop.kind)


def field_help(prop: Property, value, values: dict, prefix: str) -> None:
    """Under a number field: a bar with the typical range and a side note in everyday terms."""
    if prop.kind not in ("float", "int") or value is None:
        return
    rock = st.session_state.get(f"{prefix}.preset.Rock type") or None if prop.key == "k_s" else None
    rng = guidance.typical(prop.key, rock, prop.label)
    if rng is not None:
        look.range_bar(float(value), rng, prop.min, prop.max, rock)
    now = {k: st.session_state.get(f"{prefix}.{k}", v) for k, v in values.items()}
    note = guidance.side_note(prop.key, float(value), now)
    if note:
        look.side_note(note)


def field_grid(props: list[Property], values: dict, prefix: str, n_cols: int) -> None:
    # on a phone the columns stack, which would mix up the order (column by column): one column there
    cols = st.columns(1 if look.is_phone() else n_cols)
    for i, prop in enumerate(props):
        with cols[i % len(cols)]:
            values[prop.key] = widget(prop, values[prop.key], f"{prefix}.{prop.key}")
            field_help(prop, values[prop.key], values, prefix)


def matching_preset(group, now: dict) -> str:
    """The choice of a drop-down whose values are the ones entered, or "" (own values)."""
    def same(a, b):
        return abs(float(a) - float(b)) < 1e-9 if isinstance(b, (int, float)) and not isinstance(b, bool) else a == b
    for option, vals in group.options.items():
        if all(k in now and same(now[k], v) for k, v in vals.items()):
            return option
    return ""


def preset_pickers(variant: Variant, key_prefix: str, values: dict) -> None:
    """Drop-downs such as "Rock type" that fill in several fields at once. They start on the choice that matches
    the values (the defaults are typical choices), or on "Own values"."""
    if not variant.presets:
        return
    now = {k: st.session_state.get(f"{key_prefix}.{k}", v) for k, v in values.items()}
    cols = st.columns(max(2, len(variant.presets)))
    for col, group in zip(cols, variant.presets):
        def apply(group=group, pick_key=f"{key_prefix}.preset.{group.label}"):
            choice = st.session_state[pick_key]
            kinds = {p.key: p.kind for p in variant.properties}
            for field, val in group.options.get(choice, {}).items():
                st.session_state[f"{key_prefix}.{field}"] = float(val) if kinds.get(field) == "float" else val
        with col:
            options = [""] + list(group.options)
            st.selectbox(f"🗂 {t(group.label)}", options, index=options.index(matching_preset(group, now)),
                         format_func=lambda o: t(o) if o else t("Own values"),
                         key=f"{key_prefix}.preset.{group.label}", on_change=apply,
                         help=t(group.help) if group.help else t("Fills in the fields below with typical values."))


def monthly_table(props: list[Property], values: dict, key: str) -> dict:
    # The columns are named by the input keys (the editor stores edits by column name); the labels follow the
    # language, so switching it keeps the edits.
    df = pd.DataFrame({p.key: list(values[p.key]) for p in props}, index=list(i18n.months()))
    st.caption(t("Monthly values. Click a cell to edit; you can paste a column from Excel."))
    edited = st.data_editor(df, key=key, width="stretch", height=35 * 13 + 3, column_config={
        p.key: st.column_config.NumberColumn(f"{t(p.label)} [{p.unit}]", help=t(p.help) or None) for p in props})
    return {p.key: [float(x) for x in edited[p.key]] for p in props}


def points_input(prop: Property, value, key: str) -> tuple:
    """Shapefile upload plus an editable coordinate table. Returns ((x, y), ...) in metres."""
    files = st.file_uploader(t("Shapefile with one point per borehole (.zip, or .shp + .shx + .dbf + .prj)"),
                             type=["zip", "shp", "shx", "dbf", "prj"], accept_multiple_files=True, key=f"{key}.upload")
    upload_id = ""
    if files:
        contents = {f.name: f.getvalue() for f in files}
        try:
            result = geometry.read_shapefile(contents)
        except geometry.GeometryError as exc:
            st.error(str(exc))
        else:
            value = result.points
            # A new upload gets a fresh table; edits made after the upload are kept.
            upload_id = hashlib.md5(b"".join(contents[n] for n in sorted(contents))).hexdigest()[:8]
            st.success(t("Read {n} boreholes from {files}.", n=len(value), files=", ".join(sorted(contents))))
            for note in result.notes:
                st.caption(note)
    df = pd.DataFrame(list(value), columns=["x [m]", "y [m]"], dtype=float)
    df.index = range(1, len(df) + 1)
    with st.expander(t("{label}: {n} boreholes (click to edit the coordinates)", label=t(prop.label), n=len(df))):
        edited = st.data_editor(df, num_rows="dynamic", height=240, width="stretch", key=f"{key}.table.{upload_id}")
    return tuple((float(x), float(y)) for x, y in edited.dropna().itertuples(index=False))


def hourly_input(prop: Property, value, key: str) -> dict:
    """Upload of an hourly heating/cooling demand file, with a template to download."""
    up_col, tpl_col = st.columns([3, 1])
    with up_col:
        file = st.file_uploader(t("Hourly demand file: 8760 rows, column 1 heating [kW], column 2 cooling [kW]"),
                                type=["csv", "txt", "xlsx"], key=f"{key}.upload")
    with tpl_col:
        template = pd.DataFrame({"heating_kW": value["heating"], "cooling_kW": value["cooling"]})
        st.download_button(t("Download template"), template.to_csv(index=False, sep=";").encode(),
                           "hourly_demand_template.csv", "text/csv", icon=":material/download:",
                           help=t("The current profile as CSV: one row per hour, heating then cooling in kW."))
    if file is not None:
        try:
            heating, cooling, notes = hourly.read_profile(file.name, file.getvalue())
        except hourly.HourlyFileError as exc:
            st.error(str(exc))
        else:
            value = {"heating": heating, "cooling": cooling}
            st.success(t("Read 8760 hours from {file}.", file=file.name))
            for note in notes:
                st.caption(note)
    elif value == hourly.example_profile():
        st.info(t("Showing an example office profile until you upload your own."), icon=":material/info:")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Heating demand"), t("{x:,.0f} MWh/yr", x=sum(value["heating"]) / 1000))
    c2.metric(t("Peak heating"), fmt("{x:,.0f} kW", x=max(value["heating"])))
    c3.metric(t("Cooling demand"), t("{x:,.0f} MWh/yr", x=sum(value["cooling"]) / 1000))
    c4.metric(t("Peak cooling"), fmt("{x:,.0f} kW", x=max(value["cooling"])))
    return value


@st.cache_resource(max_entries=64, show_spinner=False)
def cached_drawing(section_key: str, variant_key: str, project_json: str, language: str) -> tuple:
    """Input drawings, cached on the inputs and the language. Matplotlib figures are stored as PNG, charts as they
    are."""
    with i18n.using(language):
        drawing = input_drawings.DRAWINGS[(section_key, variant_key)][1](model.from_json(project_json)[1])
    parts = []
    for part in drawing if isinstance(drawing, tuple) else (drawing,):
        if isinstance(part, plt.Figure):
            buf = io.BytesIO()
            part.savefig(buf, format="png", dpi=110, bbox_inches="tight")
            plt.close(part)
            parts.append(buf.getvalue())
        else:
            parts.append(part)
    return tuple(parts)


def show_drawing(parts: tuple) -> None:
    for part in parts:
        if isinstance(part, bytes):
            st.image(part, width="stretch")
        else:
            chart(part)


def chart(c, width="stretch") -> None:
    look.show_chart(c, width)
