"""Streamlit page. Start with:  streamlit run app.py"""
import hashlib
import html
import io
import pathlib
import sys

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st


def _drop_stale_package():
    """After a deploy the server reruns app.py but keeps the old ghe_web modules in memory, which crashes
    the page. When any ghe_web file changed since it was imported, forget the old modules and cached results."""
    stamp = tuple(sorted((str(p), p.stat().st_mtime_ns) for p in (pathlib.Path(__file__).parent / "ghe_web").rglob("*.py")))
    loaded = sys.modules.get("ghe_web")
    if loaded is not None and getattr(loaded, "_stamp", None) != stamp:
        for name in [m for m in sys.modules if m == "ghe_web" or m.startswith("ghe_web.")]:
            del sys.modules[name]
        st.cache_data.clear()
        st.cache_resource.clear()
    import ghe_web
    ghe_web._stamp = stamp


_drop_stale_package()

from ghe_web import analysis, export, geometry, hourly, i18n, model, plots, properties, report
from ghe_web.i18n import fmt, t
from ghe_web.siteplan import page as siteplan_page
from ghe_web.strata import page as strata_page
from ghe_web.properties import Property, SectionInput, Variant

st.set_page_config(page_title="GHEtool Web", page_icon="🌍", layout="wide")
st.markdown("""<style>
.block-container {padding-top: 2rem;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
table.keys {width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0;}
table.keys td {border: none; border-bottom: 1px solid rgba(128,128,128,0.18); padding: 6px 4px; vertical-align: top;}
table.keys tr:last-child td {border-bottom: none;}
table.keys td.val {text-align: right; font-weight: 600; white-space: nowrap; padding-left: 12px;}
table.keys .note {font-size: 0.78rem; opacity: 0.65; line-height: 1.25;}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------------- language (first, so everything below follows it)

if "pending_language" in st.session_state:  # set by opening a project file
    st.session_state.language = st.session_state.pop("pending_language")
# At the top of the page (not in the sidebar), so it is also visible on phones where the sidebar starts closed.
title_col, language_col = st.columns([5, 1.3], vertical_alignment="center")
with language_col:
    lang = st.segmented_control("🌐 Language · Sprache", list(i18n.LANGUAGES), format_func=i18n.LANGUAGES.get,
                                default=i18n.DEFAULT, required=True, key="language")
lang = i18n.set_language(lang)
if st.session_state.get("shown_language", lang) != lang:
    # The browser sends choices back as their shown label, which is now in the other language, so Streamlit would
    # reset them. Writing the values back first keeps every choice (radios, drop-downs, view switches).
    for k, v in list(st.session_state.items()):
        if k == "language":
            continue
        if isinstance(v, (str, int)) and not isinstance(v, bool) or isinstance(v, list) and v and \
                all(isinstance(x, (str, int)) for x in v):
            st.session_state[k] = v
st.session_state.shown_language = lang


def in_language(fn, *args):
    """For downloads made when the button is clicked: they run outside this page run, so they get the language."""
    return lambda: i18n.call_in(lang, fn, *args)


def chart(c) -> None:
    st.altair_chart(i18n.localize_chart(c), width="stretch")


# Input steps, in page order. A section with an unknown group lands in "More inputs", so new
# sections show up without changes here. The tab labels follow the language; the ids stay the same.
STEP_LABELS = {"site_plan": "⓪ Site plan", "Site": "① Ground & borefield", "Borehole": "② Borehole & fluid",
               "Loads": "③ Loads", "Design": "④ Limits & calculation", "more": "More inputs", "results": "📊 Results"}
STEPS = {k: t(v) for k, v in STEP_LABELS.items()}
SITE_PLAN, MORE, RESULTS = STEPS["site_plan"], STEPS["more"], STEPS["results"]

# Values the widgets start from: the defaults, or a project the user loaded.
# Widget keys include a generation number, so loading a project rebuilds every widget.
if "project" not in st.session_state:
    st.session_state.project = ("", model.default_inputs())
    st.session_state.generation = 0
project_name, start = st.session_state.project
gen = st.session_state.generation
if st.session_state.pop("goto_results", False):
    st.session_state.step = RESULTS
if "goto_step" in st.session_state:
    st.session_state.step = STEPS[st.session_state.pop("goto_step")]
if st.session_state.get("step") not in (None, *STEPS.values()):  # the language changed: same tab, new label
    for code in i18n.LANGUAGES:
        with i18n.using(code):
            match = [k for k, v in STEP_LABELS.items() if t(v) == st.session_state.step]
        if match:
            st.session_state.step = STEPS[match[0]]
            break
    else:
        del st.session_state.step


# ---------------------------------------------------------------- sidebar: save / load

with st.sidebar:
    st.header(t("Project"))
    name = st.text_input(t("Project name"), value=project_name, key=f"{gen}.name")
    uploaded = st.file_uploader(t("Open a saved project"), type="json", key=f"{gen}.upload")
    if uploaded is not None:
        text = uploaded.getvalue().decode()
        try:
            st.session_state.project = model.from_json(text)
        except Exception as exc:
            st.error(t("Could not open this file: {error}", error=exc))
        else:
            saved = model.saved_language(text)
            if saved in i18n.LANGUAGES:
                st.session_state.pending_language = saved
            st.session_state.generation += 1
            st.rerun()
    save_slot = st.empty()  # filled after the inputs are read
    st.caption(t("Projects are saved as a file on your computer, including the language. Nothing is stored on "
                 "the server."))
    st.caption(t("🌙 Dark mode: menu **⋮** at the top right > **Settings** > theme **Dark**."))
    st.divider()
    calc_slot = st.container()  # the calculate button and a short result, filled at the end

title_col.title(t("Borehole heat exchanger sizing"))
st.caption(t("Fill in the four input steps, then press **Size borefield** on the left. Every field has a question "
             "mark with an explanation; the drop-downs fill in typical values."))
with st.expander(t("How to use this tool"), icon=":material/help:"):
    st.markdown(t(
        "1. **⓪ Site plan** (optional): find the parcel and place as many boreholes as fit.\n"
        "2. **① Ground & borefield**: ground properties (or predicted layers) and the borefield layout.\n"
        "3. **② Borehole & fluid**: borehole heat exchanger, heat transfer fluid and flow rate.\n"
        "4. **③ Loads**: the heat extracted from and injected into the ground, or the building demand with the "
        "heat pump efficiency.\n"
        "5. **④ Limits & calculation**: the allowed fluid temperatures, and whether to size the length or check a "
        "given one.\n"
        "6. Press **Size borefield** in the sidebar. The **📊 Results** tab shows key figures, charts, further "
        "analysis and the PDF report and Excel export.\n\n"
        "Save the project in the sidebar to continue later. Calculations use the open-source "
        "[GHEtool](https://github.com/wouterpeere/GHEtool)."))


# ---------------------------------------------------------------- inputs

def widget(prop: Property, value, key: str):
    label = f"{t(prop.label)} [{t(prop.unit)}]" if prop.unit else t(prop.label)
    # A preset may already have put a value in the session state; then the widget must not get one too.
    initial = {} if key in st.session_state else None
    help_text = t(prop.help) or None
    if prop.kind == "float":
        kw = initial if initial is not None else {"value": float(value)}
        as_float = lambda x: float(x) if x is not None else None  # noqa: E731 (Streamlit refuses mixed int/float)
        return st.number_input(label, min_value=as_float(prop.min), max_value=as_float(prop.max),
                               step=as_float(prop.step), help=help_text, key=key, **kw)
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


def preset_pickers(variant: Variant, key_prefix: str) -> None:
    """Drop-downs such as "Rock type" that fill in several fields at once."""
    if not variant.presets:
        return
    cols = st.columns(max(2, len(variant.presets)))
    for col, group in zip(cols, variant.presets):
        def apply(group=group, pick_key=f"{key_prefix}.preset.{group.label}"):
            choice = st.session_state[pick_key]
            kinds = {p.key: p.kind for p in variant.properties}
            for field, val in group.options.get(choice, {}).items():
                st.session_state[f"{key_prefix}.{field}"] = float(val) if kinds.get(field) == "float" else val
        with col:
            st.selectbox(f"🗂 {t(group.label)}", [""] + list(group.options),
                         format_func=lambda o: t(o) if o else t("Choose to fill in typical values…"),
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
        drawing = plots.DRAWINGS[(section_key, variant_key)][1](model.from_json(project_json)[1])
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


def borehole_depth() -> tuple[float, float]:
    """Borehole length and buried depth as currently entered (the borefield section may come later on the page),
    for sections that need them before it is read."""
    chosen = start.get("borefield") or SectionInput("rectangular", {})
    section = properties.get("borefield")
    variant = st.session_state.get(f"{gen}.borefield.variant_key", chosen.variant)
    defaults = {**section.variant(variant).defaults(), **(chosen.values if variant == chosen.variant else {})}
    return (float(st.session_state.get(f"{gen}.borefield.{variant}.H", defaults["H"])),
            float(st.session_state.get(f"{gen}.borefield.{variant}.D", defaults["D"])))


def section_inputs(section) -> tuple[SectionInput, object]:
    """Draws one section and returns its values and where its drawing goes (or None)."""
    with st.container(border=True):
        st.markdown(f"##### {t(section.label)}")
        if section.help:
            st.caption(t(section.help))
        chosen = start.get(section.key) or SectionInput(section.variant().key, section.variant().defaults())
        variant = section.variant(chosen.variant)
        if len(section.variants) > 1:
            keys = [v.key for v in section.variants]
            picked = st.radio(t("Input method"), keys, index=keys.index(variant.key), horizontal=True,
                              format_func=lambda k: t(section.variant(k).label),
                              key=f"{gen}.{section.key}.variant_key")
            variant = section.variant(picked)
        if variant.help:
            st.caption(t(variant.help))
        values = variant.defaults()
        if variant.key == chosen.variant:
            values.update(chosen.values)
        simple = [p for p in variant.properties if p.kind not in ("monthly", "points", "hourly", "layers")]
        layer_props = [p for p in variant.properties if p.kind == "layers"]
        point_props = [p for p in variant.properties if p.kind == "points"]
        hourly_props = [p for p in variant.properties if p.kind == "hourly"]
        monthly = [p for p in variant.properties if p.kind == "monthly"]
        # wide inputs (tables, hourly files) get their drawing below instead of beside them
        has_drawing = (section.key, variant.key) in plots.DRAWINGS
        side = has_drawing and not monthly and not hourly_props
        form_col, drawing_col = st.columns([3, 2], gap="large") if side else (st.container(), None)
        prefix = f"{gen}.{section.key}.{variant.key}"
        with form_col:
            preset_pickers(variant, prefix)
            for prop in hourly_props:
                values[prop.key] = hourly_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            for prop in point_props:
                values[prop.key] = points_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            cols = st.columns(2 if side else 3)
            for i, prop in enumerate(simple):
                with cols[i % len(cols)]:
                    values[prop.key] = widget(prop, values[prop.key], f"{prefix}.{prop.key}")
            if monthly:
                values.update(monthly_table(monthly, values, f"{prefix}.monthly"))
        for prop in layer_props:  # full width below the fields and the drawing
            values[prop.key] = strata_page.layers_input(prop, values[prop.key], f"{prefix}.{prop.key}", prefix,
                                                        *borehole_depth())
        problems = variant.validate(values)
        for msg in problems:
            st.error(msg, icon=":material/error:")
        if not problems:
            for msg in variant.check_warnings(values):
                st.warning(msg, icon=":material/warning:")
        notes[section.key] = st.empty()  # filled once all sections are read (warnings that need other sections)
        target = drawing_col if side else (st.container() if has_drawing else None)
    return SectionInput(variant.key, values), target


grouped: dict[str, list] = {}
for section in properties.sections():
    grouped.setdefault(STEPS.get(section.group, MORE), []).append(section)
step_names = [SITE_PLAN] + [s for s in [STEPS[k] for k in ("Site", "Borehole", "Loads", "Design")] + [MORE]
                            if s in grouped] + [RESULTS]
step_tabs = dict(zip(step_names, st.tabs(step_names, default=STEPS["Site"], key="step", on_change="rerun")))

inputs: dict[str, SectionInput] = {}
notes: dict[str, object] = {}
section_step: dict[str, str] = {}
pending_drawings = []  # (where, section, variant), drawn once every section is read
for step, sections in grouped.items():
    with step_tabs[step]:
        if step == STEPS["Site"] and "site_plan_done" in st.session_state:
            st.success(t("Borefield set to an irregular field with the {n} positions from the site plan.",
                         n=st.session_state.pop("site_plan_done")), icon=":material/check_circle:")
        for section in sections:
            inputs[section.key], target = section_inputs(section)
            section_step[section.key] = step
            # Drawn later because some drawings use other sections too
            # (the borehole picture needs the radius from "Borefield").
            if target is not None:
                pending_drawings.append((target, section.key, inputs[section.key].variant))

errors = model.validate(inputs)
for section_key, msgs in model.cross_warnings(inputs).items():
    with notes[section_key].container():
        for msg in msgs:
            st.info(msg, icon=":material/info:")
current_json = model.to_json(inputs)
for target, section_key, variant_key in pending_drawings:
    if section_key in errors or "borefield" in errors:
        continue
    with target:
        show_drawing(cached_drawing(section_key, variant_key, current_json, lang))


def use_site_plan(points) -> None:
    """Called from the site plan: the borefield becomes an irregular field with these positions."""
    st.session_state.site_plan_points = points
    st.rerun()


if "site_plan_points" in st.session_state:
    pts = st.session_state.pop("site_plan_points")
    x0, y0 = min(x for x, _ in pts), min(y for _, y in pts)
    borefield = inputs["borefield"]
    values = dict(borefield.values) if borefield.variant == "custom" else \
        {**properties.get("borefield").variant("custom").defaults(),
         **{k: v for k, v in borefield.values.items() if k in ("H", "D", "r_b_mm")}}
    values["points"] = tuple((round(x - x0, 2), round(y - y0, 2)) for x, y in pts)
    st.session_state.project = (name, {**inputs, "borefield": SectionInput("custom", values)})
    st.session_state.generation += 1
    st.session_state.goto_step = "Site"
    st.session_state.site_plan_done = len(pts)
    st.rerun()

with step_tabs[SITE_PLAN]:
    # Only drawn while open: the map and the data services are slow.
    if st.session_state.get("step") == SITE_PLAN:
        siteplan_page.page(use_site_plan)

with save_slot:
    st.download_button(t("Save project"), model.to_json(inputs, name, language=lang).encode(),
                       f"{name.strip() or 'ghetool-project'}.json", "application/json", width="stretch",
                       icon=":material/save:")


# ---------------------------------------------------------------- calculation

@st.cache_resource(max_entries=16, show_spinner=False)
def cached_size(project_json: str) -> model.SizingResult:
    """Sizing is cached on the exact inputs, so going back to earlier inputs is instant."""
    return model.size(model.from_json(project_json)[1])


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_sensitivity(project_json: str) -> pd.DataFrame:
    return analysis.sensitivity(model.from_json(project_json)[1])


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_optimisation(project_json: str, *limits) -> pd.DataFrame:
    return analysis.optimise_layout(model.from_json(project_json)[1], *limits)


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_load_optimisation(project_json: str, objective: str) -> dict | None:
    return analysis.load_optimisation(cached_size(project_json), objective)


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_ground_map(project_json: str) -> dict | None:
    return analysis.ground_temperature_map(cached_size(project_json))


mode_check = inputs["calculation"].variant == "check"
action = t("Check temperatures") if mode_check else t("Size borefield")


def calculate() -> None:
    slow = model.temperature_dependent_cop(inputs) and inputs["load"].values.get("hourly_sizing")
    with st.spinner(t("Calculating... hourly sizing with a temperature-dependent COP takes one to two minutes.")
                    if slow else t("Calculating... hourly sizing can take up to a minute.")):
        try:
            cached_size(current_json)
        except Exception as exc:  # show GHEtool errors to the user instead of crashing
            st.session_state.pop("result_json", None)
            st.session_state.calc_error = str(exc)
        else:
            st.session_state.result_json = current_json
            st.session_state.pop("calc_error", None)
            st.session_state.goto_results = True
    st.rerun()


with calc_slot:
    st.header(t("Calculation"))
    if errors:
        st.error(t("{n} input(s) need attention:", n=sum(len(m) for m in errors.values())) + "\n\n" + "\n".join(
            f"- {section_step.get(k, '')}: {t(properties.get(k).label)}" for k in errors), icon=":material/error:")
    if st.button(action, type="primary", disabled=bool(errors), width="stretch", icon=":material/calculate:"):
        calculate()
    if "calc_error" in st.session_state:
        st.error(t("The calculation failed: {error}", error=st.session_state.calc_error))
    if "result_json" in st.session_state:
        res = cached_size(st.session_state.result_json)
        st.metric(t("Borehole length") if res.sizing_method == "check" else t("Required borehole length"),
                  fmt("{x:.1f} m", x=res.borehole_length),
                  t("{n} boreholes, {total:,.0f} m in total", n=res.number_of_boreholes, total=res.total_length),
                  delta_color="off", delta_arrow="off")
        if st.session_state.result_json != current_json:
            st.warning(t("The inputs changed since the last calculation."), icon=":material/update:")
        else:
            st.caption(t("See the **📊 Results** tab for details."))


# ---------------------------------------------------------------- results

def key_table(rows: list[tuple[str, str, str]]) -> None:
    """A compact two-column table: item with its note underneath, and the value."""
    body = "".join(
        f"<tr><td>{html.escape(label)}<div class='note'>{html.escape(note)}</div></td>"
        f"<td class='val'>{html.escape(value)}</td></tr>" for label, value, note in rows)
    st.markdown(f"<table class='keys'>{body}</table>", unsafe_allow_html=True)


def sensitivity_table(sens: pd.DataFrame) -> pd.DataFrame:
    table = sens.rename(columns={"Input": t("Input"), "Low": t("Input lower [m]"), "High": t("Input higher [m]"),
                                 "Base": t("Base [m]"), "Spread": t("Spread [m]")})
    table[t("Input")] = table[t("Input")].map(t)
    return table


def layout_table(table: pd.DataFrame) -> pd.DataFrame:
    table = table.copy()
    table["Layout"] = table["Layout"].map(t)
    return table.rename(columns=t)


def extra_tables(sized_json: str) -> dict[str, pd.DataFrame]:
    """Analysis the user ran for this result, so the export contains it too."""
    extra = {}
    if st.session_state.get("sensitivity_json") == sized_json:
        extra[t("Sensitivity")] = sensitivity_table(cached_sensitivity(sized_json))
    if st.session_state.get("kept"):
        extra[t("Variant comparison")] = pd.DataFrame(st.session_state.kept).rename(columns=t)
    if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
        extra[t("Layout optimisation")] = layout_table(st.session_state.optimised)
    opt = load_optimisation_done(sized_json)
    if opt is not None:
        monthly = opt["monthly"].round(3)
        monthly["Month"] = list(i18n.months())
        extra[t("Load optimisation, monthly")] = monthly.rename(columns=t)
        extra[t("Load optimisation, yearly")] = opt["yearly"].round(3).rename(columns=t)
    return extra


def load_optimisation_done(sized_json: str) -> dict | None:
    """The load optimisation the user ran for this result, if any."""
    ran = st.session_state.get("load_opt")
    if ran and ran[0] == sized_json:
        return cached_load_optimisation(sized_json, ran[1])
    return None


def view_overview(result, key, limits) -> None:
    if result.hourly_basis:  # the hourly result is what the limits were checked against
        chart(plots.hourly_band_chart(result.hourly_temperatures, limits))
        st.caption(t("Daily range of the hourly average fluid temperature. Dashed: your limits."))
    else:
        chart(plots.temperature_chart(result.temperatures, limits))
        st.caption(t("Blue: coldest fluid (heating peaks). Red: warmest fluid (cooling peaks). Dashed: your limits. "
                     "Grey dots: the lowest and highest value."))
    # spread the groups over two columns so both end at about the same height
    parts, heights = ([], []), [0, 0]
    for group, rows in key.by_group().items():
        side = heights.index(min(heights))
        parts[side].append((group, rows))
        heights[side] += len(rows) + 1
    for col, part in zip(st.columns(2, gap="large"), parts):
        with col:
            for group, rows in part:
                with st.container(border=True):
                    st.markdown(f"**{group}**")
                    key_table(rows)


TEMP_VIEWS = {"years": "Over the years", "last": "Last year", "extremes": "Yearly min/max", "table": "Table"}


def view_temperatures(result, limits) -> None:
    if result.hourly_basis:
        st.info(t("These are the monthly temperatures with block peaks, shown for comparison. The sizing checked "
                  "the limits hour by hour: see **Hourly** for those temperatures."), icon=":material/info:")
    choice = st.segmented_control(t("Chart"), list(TEMP_VIEWS), format_func=lambda k: t(TEMP_VIEWS[k]),
                                  default="years", required=True, key="temp_view_id")
    if choice == "years":
        chart(plots.temperature_chart(result.temperatures, limits))
    elif choice == "last":
        chart(plots.last_year_chart(result.temperatures, limits))
        if "Into borefield (peak extraction)" in result.temperatures:
            st.caption(t("Into the borefield = supply from the heat pump; out of the borefield = return to the heat "
                         "pump."))
    elif choice == "extremes":
        chart(plots.yearly_extremes_chart(analysis.yearly_extremes(result), limits))
        st.caption(t("If the lowest temperature keeps falling (or the highest keeps rising) every year, the ground "
                     "is out of balance. A longer simulation period shows whether it levels off."))
    else:
        st.dataframe(export.monthly_temperatures(result).round(2), hide_index=True, width="stretch", height=420)


def view_energy(result, key) -> None:
    energy = analysis.monthly_ground_energy(result)
    chart(plots.energy_balance_chart(energy))
    st.caption(t("Energy taken from (heating) and put into (cooling) the ground, after heat pump efficiency."))
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Extracted from the ground"), t("{x:,.0f} MWh/yr", x=key.values["extraction_mwh"]))
    c2.metric(t("Injected into the ground"), t("{x:,.0f} MWh/yr", x=key.values["injection_mwh"]))
    c3.metric(t("Imbalance"), t("{x:+,.0f} MWh/yr", x=key.values["imbalance_mwh"]))
    duration = analysis.load_duration(result)
    if duration is not None:
        chart(plots.load_duration_chart(duration))
        st.caption(t("Each load sorted from its highest hour to its lowest. Solid: building demand. Dashed: what the "
                     "ground sees after the heat pump. The area under a curve is the energy per year."))


def view_hydraulics(result, key) -> None:
    if result.reynolds is None:
        st.info(t("With a measured borehole resistance (TRT) the pipe and flow are not known, so there are no "
                  "hydraulic results."), icon=":material/info:")
        return
    v = key.values
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Borehole thermal resistance Rb"), fmt("{x:.3f} m·K/W", x=result.borehole_resistance))
    c2.metric(t("Reynolds number"), fmt("{x:,.0f}", x=v["Re"]), analysis.regime(v["Re"]), delta_color="off",
              delta_arrow="off")
    if "dp_kpa" in v:
        c3.metric(t("Pressure drop per borehole"), fmt("{x:.1f} kPa", x=v["dp_kpa"]))
        c4.metric(t("Pump power"), fmt("{x:,.0f} W", x=v["pump_electric_w"]),
                  t("{x:,.1f} MWh per year", x=v["pump_mwh"]), delta_color="off", delta_arrow="off")
        curve = analysis.pressure_drop_curve(result, v["t_min"])
        if curve is not None:
            bf = result.borefield
            flow = float(bf.borehole.flow_data.vfr_borehole(fluid_data=bf.borehole.fluid_data,
                                                             temperature=v["t_min"]))
            chart(plots.pressure_drop_chart(curve, flow, v["dp_kpa"]))
            st.caption(t("At the coldest fluid temperature, where the fluid is most viscous. The borehole only: add "
                         "the manifold, header pipes and heat pump evaporator for the pump. The kink is where the "
                         "flow turns turbulent."))
    st.caption(t("Pump energy = hydraulic power ÷ pump efficiency × operating hours, both set under Flow rate in "
                 "step ②."))


def view_ground(result, sized_json) -> None:
    with st.spinner(t("Calculating the ground temperature around the field...")):
        m = cached_ground_map(sized_json)
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Undisturbed ground"), fmt("{x:.1f} °C", x=m["t_ground"]))
    c2.metric(t("Net heat flow into the ground"), fmt("{x:+.2f} W/m", x=m["q_w_per_m"]),
              t("yearly average per metre of borehole"), delta_color="off", delta_arrow="off")
    c3.metric(t("Largest change"), fmt("{x:.1f} K", x=m["max_change"]), t("after {n} years", n=m["years"]),
              delta_color="off", delta_arrow="off")
    left, right = st.columns([3, 2])
    with left:
        chart(plots.ground_map_chart(m))
    with right:
        st.caption(t("How the yearly imbalance warms (red) or cools (blue) the ground around the field at the end "
                     "of the simulation, halfway down the boreholes. Each dot is a borehole. Boreholes in the middle "
                     "change most because their neighbours add up. The seasonal swing on top of this averages out "
                     "over a year and is left out."))
        st.caption(t("Calculated with the finite line source (uniform heat flow per metre, with the mirror image at "
                     "the surface), which is also the basis of the g-function."))
    with st.expander(t("g-function (for specialists)"), icon=":material/show_chart:"):
        st.caption(t("The dimensionless step response of the field. Its rise at large times shows how strongly the "
                     "boreholes influence each other."))
        chart(plots.gfunction_chart(analysis.gfunction_curve(result)))


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_uniform(project_json: str) -> tuple[float, float]:
    """The same design sized with one average conductivity and heat capacity instead of the layers."""
    return analysis.uniform_ground_length(cached_size(project_json), model.from_json(project_json)[1])


def view_layers(result, sized_inputs, sized_json) -> None:
    from ghe_web.strata import predict
    rows, used = plots.ground_rows(sized_inputs)
    length, buried = result.borehole_length, sized_inputs["borefield"].values["D"]
    k, c = predict.effective(rows, length, buried)
    parts = predict.contributions(rows, length, buried)
    if not used:
        st.info(t("These layers were not used: the calculation took the single conductivity from step ①. Switch on "
                  "**Calculate with the layers** under Ground to size with them."), icon=":material/info:")
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Average conductivity along the borehole"), fmt("{x:.2f} W/(m·K)", x=k),
              t("from {top:.1f} to {bottom:.0f} m", top=buried, bottom=buried + length), delta_color="off",
              delta_arrow="off")
    c2.metric(t("Average heat capacity"), fmt("{x:.2f} MJ/(m³·K)", x=c))
    c3.metric(t("Layers reached"), t("{n} of {total}", n=len(parts), total=len(rows)))
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.pyplot(plots.borehole_log(rows, length, buried, t("{n} boreholes of {length:.1f} m",
                                                             n=result.number_of_boreholes, length=length)),
                  width="stretch")
    with right:
        st.markdown(t("**Share of the heat exchange per layer**"))
        chart(plots.layer_share_chart(parts))
        st.caption(t("Length in the layer × its conductivity, as a share of the whole borehole. Layers that conduct "
                     "well carry more of the heat, so they are worth reaching."))
        st.markdown(t("**Average conductivity for other borehole lengths**"))
        top = max(float(rows[-1]["top"]) * 1.2, length * 1.6, 50.0)
        chart(plots.conductivity_with_length(rows, buried, range(10, int(top) + 1, 5), length))
        st.caption(t("Dashed: the calculated length. Where the curve rises, a deeper borehole reaches better "
                     "ground."))
    if used:
        with st.expander(t("Compare: the same design with one average value"), icon=":material/compare_arrows:"):
            st.caption(t("Sizes again with a single conductivity and heat capacity, the average over the borehole "
                         "length found here. The difference shows how much the layering matters."))
            if st.button(t("Calculate the comparison"), key="uniform_go"):
                st.session_state.uniform_json = sized_json
            if st.session_state.get("uniform_json") == sized_json:
                with st.spinner(t("Sizing with the average values...")):
                    try:
                        uniform, k_used = cached_uniform(sized_json)
                    except Exception as exc:
                        st.error(t("The comparison failed: {error}", error=exc))
                        return
                d1, d2 = st.columns(2)
                d1.metric(t("With layers"), fmt("{x:.1f} m", x=length))
                d2.metric(t("With one value ({k:.2f} W/(m·K))", k=k_used), fmt("{x:.1f} m", x=uniform),
                          t("{x:+.1f} m per borehole", x=uniform - length), delta_color="off", delta_arrow="off")


def view_load_optimisation(result, sized_json) -> None:
    st.caption(t("Keeps the borefield as designed and works out how much of the hourly building demand it can take "
                 "within the temperature limits. The rest comes from a backup boiler, gas or electric, or a chiller "
                 "(a hybrid system). This answers: how far does a smaller or cheaper field get me?"))
    names = analysis.OBJECTIVES
    with st.form("load_opt_form"):
        objective = st.radio(t("Optimise for"), list(names), format_func=lambda k: t(names[k]), horizontal=True,
                             captions=[t("the largest share of the peak power"), t("the most energy, month by month"),
                                       t("the most power with no long-term imbalance (slow, 2 to 3 minutes)")])
        go = st.form_submit_button(t("Optimise the load"), icon=":material/tune:", type="primary")
    if go:
        with st.spinner(t("Optimising the load split...")):
            try:
                cached_load_optimisation(sized_json, objective)
                st.session_state.load_opt = (sized_json, objective)
            except Exception as exc:
                st.error(t("The optimisation failed: {error}", error=exc))
    opt = load_optimisation_done(sized_json)
    if opt is None:
        return
    st.markdown(t("**Result: {objective}**", objective=t(names[opt["objective"]])))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Heating covered by the ground"), fmt("{x:.1%}", x=opt["heating_share"]))
    k2.metric(t("Cooling covered by the ground"), fmt("{x:.1%}", x=opt["cooling_share"]))
    k3.metric(t("Backup heating"), fmt("{x:,.0f} kW", x=opt["backup_heating_kw"]),
              t("{x:,.1f} MWh per year", x=opt["backup_heating_mwh"]), delta_color="off", delta_arrow="off")
    k4.metric(t("Backup cooling"), fmt("{x:,.0f} kW", x=opt["backup_cooling_kw"]),
              t("{x:,.1f} MWh per year", x=opt["backup_cooling_mwh"]), delta_color="off", delta_arrow="off")
    chart(plots.optimisation_chart(opt["monthly"]))
    st.caption(t("Peak power taken by the ground: heating {heat:,.0f} kW, cooling {cool:,.0f} kW (building side).",
                 heat=opt["ground_peak_heating_kw"], cool=opt["ground_peak_cooling_kw"]))
    stem = name.strip() or "ghetool-project"
    st.download_button(t("Download the optimised load, first year hourly (CSV)"),
                       lambda: opt["first_year"].round(3).to_csv().encode(), f"{stem}_optimised_load.csv",
                       "text/csv", icon=":material/download:", on_click="ignore")


HOURLY_VIEWS = {"daily": "Daily range", "last": "Last year", "heatmap": "Heat map"}


def view_hourly(result, limits) -> None:
    choice = st.segmented_control(t("Chart"), list(HOURLY_VIEWS), format_func=lambda k: t(HOURLY_VIEWS[k]),
                                  default="daily", required=True, key="hourly_view_id")
    if choice == "daily":
        chart(plots.hourly_band_chart(result.hourly_temperatures, limits))
    elif choice == "last":
        chart(plots.hourly_last_year_chart(result.hourly_temperatures, limits))
        st.caption(t("The band spans the lowest and highest fluid temperature of every 3 hours, so all peaks are "
                     "visible."))
    else:
        chart(plots.heatmap_chart(result.hourly_temperatures))
        st.caption(t("Each cell is one hour of the last year. Blue is cold, red is warm."))


def view_heat_pump(result, key, sized_inputs) -> None:
    curve = sized_inputs["heat_pump"].variant == "curve"
    c1, c2, c3 = st.columns(3)
    if "spf_heating" in key.values:
        c1.metric(t("SPF heating"), fmt("{x:.2f}", x=key.values["spf_heating"]),
                  t("{x:+.2f} from year 1 to the last year", x=key.values["spf_last"] - key.values["spf_first"])
                  if curve else None, delta_color="off", delta_arrow="off")
    if "seer" in key.values:
        c2.metric(t("SEER cooling"), fmt("{x:.1f}", x=key.values["seer"]))
    c3.metric(t("Electricity per year"), fmt("{x:,.1f} MWh", x=key.values["electricity_mwh"]))
    if curve:
        lo = float(min(result.temperatures["Average fluid (peak extraction)"].min(), key.values["t_min"]))
        hi = float(max(result.temperatures["Average fluid (peak injection)"].max(), key.values["t_max"]))
        for c in plots.efficiency_curves(sized_inputs["heat_pump"].values, (lo, hi)):
            chart(c)
    else:
        st.info(t("The heat pump efficiency is fixed (SCOP/SEER). Choose **Depends on the fluid temperature** under "
                  "Heat pump efficiency in step ③ to see how the COP changes as the ground cools."),
                icon=":material/info:")
    charts = plots.heat_pump_yearly_chart(result.heat_pump, show_spf=curve)
    for c in charts if isinstance(charts, tuple) else (charts,):
        chart(c)


def view_analysis(result, key, sized_json, sized_inputs) -> None:
    with st.expander(t("Sensitivity check: what the borehole length depends on"), icon=":material/tune:"):
        st.caption(t("Sizes the field again with one input changed at a time (monthly sizing for speed). The longest "
                     "bars are the inputs worth measuring carefully, e.g. with a thermal response test."))
        if st.button(t("Run the sensitivity check")):
            st.session_state.sensitivity_json = sized_json
        if st.session_state.get("sensitivity_json") == sized_json:
            with st.spinner(t("Sizing the variations...")):
                sens = cached_sensitivity(sized_json)
            chart(plots.tornado_chart(sens))
            base = float(sens["Base"].iloc[0])
            table = pd.DataFrame({t("Input"): sens["Input"].map(t),
                                  t("Length, input lower [m]"): sens["Low"],
                                  t("Length, input higher [m]"): sens["High"],
                                  t("Change, lower [%]"): (sens["Low"] / base - 1) * 100,
                                  t("Change, higher [%]"): (sens["High"] / base - 1) * 100})
            st.dataframe(table.round(1), hide_index=True)
            if result.sizing_method != "monthly":
                st.caption(t("The variations use monthly sizing, which gives {base:.1f} m for these inputs (the "
                             "result above: {length:.1f} m). Read the changes in percent.", base=base,
                             length=result.borehole_length))

    with st.expander(t("Compare variants"), icon=":material/compare_arrows:"):
        st.caption(t("Keep this result, change the inputs, size again and keep that one too. The comparison stays "
                     "until you close the page and is part of the Excel export."))
        label_col, button_col = st.columns([3, 1], vertical_alignment="bottom")
        variant_name = label_col.text_input(t("Name for this result"),
                                            value=t("Variant {n}", n=len(st.session_state.get("kept", [])) + 1))
        if button_col.button(t("Keep this result"), width="stretch", icon=":material/push_pin:"):
            row = {"Variant": variant_name, "Boreholes": result.number_of_boreholes,
                   "Length each [m]": round(result.borehole_length, 1), "Total length [m]": round(result.total_length),
                   "Lowest temp. [°C]": round(key.values["t_min"], 2),
                   "Highest temp. [°C]": round(key.values["t_max"], 2),
                   "Rb [m·K/W]": round(result.borehole_resistance, 3)}
            st.session_state.setdefault("kept", []).append(row)
        kept = st.session_state.get("kept", [])
        if kept:
            table = pd.DataFrame(kept)
            st.dataframe(table.rename(columns=t), hide_index=True, width="stretch")
            chart(plots.comparison_chart(table, "Total length [m]", t("Total length [m]")))
            if st.button(t("Clear the comparison")):
                st.session_state.kept = []
                st.rerun()

    with st.expander(t("Optimise the layout for a plot"), icon=":material/grid_view:"):
        st.caption(t("Searches rectangular, L, U, box and staggered fields that fit in the plot and meet the "
                     "temperature limits, and lists the ones with the least drilling. Each trial takes a few "
                     "seconds."))
        with st.form("optimise"):
            o1, o2, o3 = st.columns(3)
            plot_l = o1.number_input(t("Plot length [m]"), 10.0, 1000.0, 70.0, 5.0)
            plot_w = o1.number_input(t("Plot width [m]"), 10.0, 1000.0, 70.0, 5.0)
            b_min = o2.number_input(t("Minimum spacing [m]"), 3.0, 20.0, 5.0, 0.5)
            b_max = o2.number_input(t("Maximum spacing [m]"), 3.0, 20.0, 8.0, 0.5)
            h_min = o3.number_input(t("Minimum borehole length [m]"), 20.0, 800.0, 50.0, 5.0)
            h_max = o3.number_input(t("Maximum borehole length [m]"), 20.0, 800.0, 150.0, 5.0)
            trials = st.slider(t("Number of trials (more finds better fields, but takes longer)"), 10, 100, 20, 5)
            go = st.form_submit_button(t("Find layouts"), icon=":material/search:")
        if go:
            with st.spinner(t("Trying {n} layouts. This takes about {minutes} minute(s)...", n=trials,
                              minutes=trials * 5 // 60 + 1)):
                try:
                    st.session_state.optimised = cached_optimisation(sized_json, plot_l, plot_w, b_min, b_max,
                                                                     h_min, h_max, trials)
                    st.session_state.optimised_json = sized_json
                except Exception as exc:
                    st.session_state.pop("optimised", None)
                    st.error(t("No layout found: {error}", error=exc))
        if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
            st.dataframe(layout_table(st.session_state.optimised.round(1)), hide_index=True, width="stretch")


REPORT_KINDS = {"full": "Full report", "summary": "One-page summary"}


def report_settings(sized_json: str, stem: str) -> tuple[report.ReportOptions, dict]:
    """Report settings in an expander. Text fields keep their values while the page is open."""
    with st.expander(t("Report settings: type, title, company, client, logo, introduction and conclusion"),
                     icon=":material/edit_document:"):
        kind = st.radio(t("Report type"), list(REPORT_KINDS), horizontal=True, key="rep_kind",
                        format_func=lambda k: t(REPORT_KINDS[k]))
        c1, c2 = st.columns(2)
        title = c1.text_input(t("Title"), key="rep_title", placeholder=stem)
        subtitle = c2.text_input(t("Subtitle"), key="rep_subtitle",
                                 placeholder=t("e.g. Borefield sizing, design phase"))
        author = c1.text_input(t("Author"), key="rep_author")
        company = c2.text_input(t("Company"), key="rep_company")
        client = c1.text_input(t("Client"), key="rep_client")
        logo = c2.file_uploader(t("Logo (PNG or JPEG)"), type=["png", "jpg", "jpeg"], key="rep_logo")
        intro = st.text_area(t("Introduction"), key="rep_intro", height=90,
                             placeholder=t("Project background, scope of the calculation..."))
        conclusion = st.text_area(t("Conclusion"), key="rep_conclusion", height=90)
        include_map = st.checkbox(t("Include the ground temperature map"), value=True, key="rep_map")
    options = report.ReportOptions(kind=kind, title=title, subtitle=subtitle, author=author, company=company,
                                   client=client, introduction=intro, conclusion=conclusion,
                                   logo=logo.getvalue() if logo else None)
    extras = {"load_optimisation": load_optimisation_done(sized_json)}
    if include_map:
        extras["ground_map"] = cached_ground_map(sized_json)
    return options, extras


def view_export(result, sized_inputs, sized_json) -> None:
    stem = name.strip() or "ghetool-project"
    extra = extra_tables(sized_json)
    included = ", ".join(extra) if extra else t("none yet; run them under Further analysis to include them")
    st.markdown(t("The files are made when you click, so the page stays fast. The PDF report and the Excel workbook "
                  "are in the language chosen in the sidebar."))
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown(t("**Excel workbook**"))
        st.caption(t("Summary, inputs, monthly and yearly temperatures, ground energy, hourly results and your "
                     "further analysis (included: {included}).", included=included))
        st.download_button(t("Download Excel (.xlsx)"), in_language(export.excel_workbook, result, sized_inputs, name,
                                                                    extra),
                           f"{stem}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", icon=":material/table_view:", on_click="ignore")
    with c2, st.container(border=True):
        st.markdown(t("**PDF report**"))
        st.caption(t("Full report: cover page, results, inputs, drawings and all charts. One-page summary: the "
                     "design, key results and the temperature chart. Fill in the report settings below first."))
        st.download_button(t("Download PDF"),
                           lambda: i18n.call_in(lang, report.make_pdf, result, sized_inputs, name, options,
                                                report_extras),
                           f"{stem}.pdf", "application/pdf", type="primary", icon=":material/picture_as_pdf:",
                           on_click="ignore")
    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        st.markdown(t("**Everything in one zip**"))
        st.caption(t("Excel workbook, PDF report and the project file, for archiving a design."))
        st.download_button(t("Download zip"),
                           lambda: i18n.call_in(lang, export.zip_bundle, result, sized_inputs, name, extra, options,
                                                report_extras),
                           f"{stem}.zip", "application/zip", icon=":material/folder_zip:", on_click="ignore")
    with c4, st.container(border=True):
        st.markdown(t("**CSV files**"))
        st.caption(t("Plain tables for other tools."))
        st.download_button(t("Monthly temperatures (CSV)"),
                           in_language(lambda: export.monthly_temperatures(result).to_csv(index=False).encode()),
                           f"{stem}_monthly.csv", "text/csv", icon=":material/download:", on_click="ignore")
        if result.hourly_temperatures is not None:
            st.download_button(t("Hourly temperatures (CSV)"),
                               lambda: result.hourly_temperatures.round(3).to_csv().encode(),
                               f"{stem}_hourly.csv", "text/csv", icon=":material/download:", on_click="ignore")
    # read when a download button is clicked, so it can come after the buttons on the page
    options, report_extras = report_settings(sized_json, stem)


RESULT_VIEWS = {"overview": "Overview", "temperatures": "Temperatures", "energy": "Energy", "hourly": "Hourly",
                "heat_pump": "Heat pump", "hydraulics": "Hydraulics", "ground": "Ground", "layers": "Layers",
                "load_optimisation": "Load optimisation", "analysis": "Further analysis", "export": "Export"}

with step_tabs[RESULTS]:
    if "result_json" not in st.session_state:
        st.info(t("No result yet. Check the inputs in the steps above, then press **{action}**.", action=action),
                icon=":material/info:")
        if st.button(action, type="primary", disabled=bool(errors), key="results_calc"):
            calculate()
    else:
        sized_json = st.session_state.result_json
        sized_inputs = model.from_json(sized_json)[1]
        result = cached_size(sized_json)
        limits = sized_inputs["limits"].values
        key = analysis.key_results(result, sized_inputs)

        if sized_json != current_json:
            st.warning(t("The inputs changed since this result was calculated. Press **{action}** to update it.",
                         action=action), icon=":material/update:")
        if result.sizing_method == "check":
            if key.values.get("passes"):
                st.success(t("The given length of {length:.0f} m keeps the fluid within the limits.",
                             length=result.borehole_length), icon=":material/check_circle:")
            else:
                st.error(t("The given length of {length:.0f} m does not keep the fluid within the limits.",
                           length=result.borehole_length), icon=":material/cancel:")
        else:
            st.success(t("{n} boreholes of {length:.1f} m keep the fluid between {t_min:g} and {t_max:g} °C for "
                         "{years} years ({method}).", n=result.number_of_boreholes, length=result.borehole_length,
                         t_min=limits["T_min"], t_max=limits["T_max"],
                         years=sized_inputs["load"].values["simulation_period"],
                         method=t(report.METHOD[result.sizing_method])),
                       icon=":material/check_circle:")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("Borehole length") if result.sizing_method == "check" else t("Required borehole length"),
                  fmt("{x:.1f} m", x=result.borehole_length))
        c2.metric(t("Total borehole length"), fmt("{x:,.0f} m", x=result.total_length),
                  t("{n} boreholes", n=result.number_of_boreholes), delta_color="off", delta_arrow="off")
        t_lo, t_hi = (round(key.values[k], 1) + 0.0 for k in ("t_min", "t_max"))  # + 0.0 avoids "-0.0"
        for col, label, temp, margin in ((c3, t("Lowest fluid temperature"), t_lo, key.values["margin_cold"]),
                                         (c4, t("Highest fluid temperature"), t_hi, key.values["margin_warm"])):
            if abs(margin) < 0.05:  # sizing stops within a few hundredths of a kelvin of the limit
                col.metric(label, fmt("{x:.1f} °C", x=temp), t("at the limit"), delta_color="off", delta_arrow="off")
            else:
                col.metric(label, fmt("{x:.1f} °C", x=temp), t("{x:+.1f} K margin", x=margin) if margin > 0 else
                           t("{x:.1f} K beyond the limit", x=-margin), delta_color="normal" if margin > 0 else "inverse")
        c5.metric(t("Borehole thermal resistance"), fmt("{x:.3f} m·K/W", x=result.borehole_resistance),
                  t("effective Rb"), delta_color="off", delta_arrow="off")
        for w in key.warnings:
            st.warning(w, icon=":material/warning:")

        views = ["overview", "temperatures", "energy"]
        if result.hourly_temperatures is not None:
            views.append("hourly")
        if result.heat_pump is not None:
            views.append("heat_pump")
        views += ["hydraulics", "ground"]
        if (sized_inputs["ground"].values.get("layers") or {}).get("rows"):
            views.append("layers")
        if sized_inputs["load"].variant == "hourly_building":
            views.append("load_optimisation")
        views += ["analysis", "export"]
        # Only the chosen view is drawn, so large hourly charts are not sent to the browser on every click.
        view = st.segmented_control(t("View"), views, format_func=lambda k: t(RESULT_VIEWS[k]), default="overview",
                                    required=True, key="result_view_id", label_visibility="collapsed")
        if view not in views:
            view = "overview"
        if view == "overview":
            view_overview(result, key, limits)
        elif view == "temperatures":
            view_temperatures(result, limits)
        elif view == "energy":
            view_energy(result, key)
        elif view == "hourly":
            view_hourly(result, limits)
        elif view == "heat_pump":
            view_heat_pump(result, key, sized_inputs)
        elif view == "hydraulics":
            view_hydraulics(result, key)
        elif view == "ground":
            view_ground(result, sized_json)
        elif view == "layers":
            view_layers(result, sized_inputs, sized_json)
        elif view == "load_optimisation":
            view_load_optimisation(result, sized_json)
        elif view == "analysis":
            view_analysis(result, key, sized_json, sized_inputs)
        else:
            view_export(result, sized_inputs, sized_json)
