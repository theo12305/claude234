"""Streamlit page. Start with:  streamlit run app.py"""
import hashlib

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ghe_web import analysis, geometry, hourly, model, plots, properties, report
from ghe_web.properties import Property, SectionInput, Variant
from ghe_web.properties.load import MONTHS

st.set_page_config(page_title="GHEtool Web", layout="wide")

# Values the widgets start from: the defaults, or a project the user loaded.
# Widget keys include a generation number, so loading a project rebuilds every widget.
if "project" not in st.session_state:
    st.session_state.project = ("", model.default_inputs())
    st.session_state.generation = 0
project_name, start = st.session_state.project
gen = st.session_state.generation


# ---------------------------------------------------------------- sidebar: save / load

with st.sidebar:
    st.header("Project")
    name = st.text_input("Project name", value=project_name, key=f"{gen}.name")
    uploaded = st.file_uploader("Open a saved project", type="json", key=f"{gen}.upload")
    if uploaded is not None:
        try:
            st.session_state.project = model.from_json(uploaded.getvalue().decode())
        except Exception as exc:
            st.error(f"Could not open this file: {exc}")
        else:
            st.session_state.generation += 1
            st.rerun()
    save_slot = st.empty()  # filled after the inputs are read
    st.caption("Projects are saved as a file on your computer. Nothing is stored on the server.")

st.title("Borehole heat exchanger sizing")


# ---------------------------------------------------------------- inputs

def widget(prop: Property, value, key: str):
    label = f"{prop.label} [{prop.unit}]" if prop.unit else prop.label
    # A preset may already have put a value in the session state; then the widget must not get one too.
    initial = {} if key in st.session_state else None
    help_text = prop.help or None
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
        return st.checkbox(label, help=help_text, key=key, **kw)
    if prop.kind == "choice":
        kw = initial if initial is not None else {"index": prop.options.index(value)}
        return st.selectbox(label, prop.options, help=help_text, key=key, **kw)
    raise ValueError(prop.kind)


def preset_pickers(variant: Variant, key_prefix: str) -> None:
    """Drop-downs such as "Rock type" that fill in several fields at once."""
    if not variant.presets:
        return
    cols = st.columns(len(variant.presets) + 1)
    for col, group in zip(cols, variant.presets):
        def apply(group=group, pick_key=f"{key_prefix}.preset.{group.label}"):
            choice = st.session_state[pick_key]
            kinds = {p.key: p.kind for p in variant.properties}
            for field, val in group.options.get(choice, {}).items():
                st.session_state[f"{key_prefix}.{field}"] = float(val) if kinds.get(field) == "float" else val
        with col:
            st.selectbox(group.label, ["Choose…"] + list(group.options), key=f"{key_prefix}.preset.{group.label}",
                         on_change=apply, help=group.help or "Fills in the fields below with typical values.")


def monthly_table(props: list[Property], values: dict, key: str) -> dict:
    df = pd.DataFrame({f"{p.label} [{p.unit}]": list(values[p.key]) for p in props}, index=MONTHS)
    edited = st.data_editor(df, key=key, width="stretch")
    return {p.key: [float(x) for x in edited.iloc[:, i]] for i, p in enumerate(props)}


def points_input(prop: Property, value, key: str) -> tuple:
    """Shapefile upload plus an editable coordinate table. Returns ((x, y), ...) in metres."""
    files = st.file_uploader("Shapefile with one point per borehole (.zip, or .shp + .shx + .dbf + .prj)",
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
            st.success(f"Read {len(value)} boreholes from {', '.join(sorted(contents))}.")
            for note in result.notes:
                st.caption(note)
    df = pd.DataFrame(list(value), columns=["x [m]", "y [m]"], dtype=float)
    df.index = range(1, len(df) + 1)
    st.caption(f"{prop.label}. You can edit, add or delete rows.")
    edited = st.data_editor(df, num_rows="dynamic", height=240, width="stretch", key=f"{key}.table.{upload_id}")
    return tuple((float(x), float(y)) for x, y in edited.dropna().itertuples(index=False))


def hourly_input(prop: Property, value, key: str) -> dict:
    """Upload of an hourly heating/cooling demand file, with a template to download."""
    up_col, tpl_col = st.columns([3, 1])
    with up_col:
        file = st.file_uploader("Hourly demand file: 8760 rows, column 1 heating [kW], column 2 cooling [kW]",
                                type=["csv", "txt", "xlsx"], key=f"{key}.upload")
    with tpl_col:
        template = pd.DataFrame({"heating_kW": value["heating"], "cooling_kW": value["cooling"]})
        st.download_button("Download template", template.to_csv(index=False, sep=";").encode(),
                           "hourly_demand_template.csv", "text/csv",
                           help="The current profile as CSV: one row per hour, heating then cooling in kW.")
    if file is not None:
        try:
            heating, cooling, notes = hourly.read_profile(file.name, file.getvalue())
        except hourly.HourlyFileError as exc:
            st.error(str(exc))
        else:
            value = {"heating": heating, "cooling": cooling}
            st.success(f"Read 8760 hours from {file.name}.")
            for note in notes:
                st.caption(note)
    elif value == hourly.example_profile():
        st.caption("Showing an example office profile until you upload your own.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Heating demand", f"{sum(value['heating']) / 1000:,.0f} MWh/yr")
    c2.metric("Peak heating", f"{max(value['heating']):,.0f} kW")
    c3.metric("Cooling demand", f"{sum(value['cooling']) / 1000:,.0f} MWh/yr")
    c4.metric("Peak cooling", f"{max(value['cooling']):,.0f} kW")
    return value


def show(drawing):
    if isinstance(drawing, tuple):  # several drawings, one below the other
        for part in drawing:
            show(part)
    elif isinstance(drawing, plt.Figure):
        st.pyplot(drawing, width="stretch")
        plt.close(drawing)
    else:
        st.altair_chart(drawing, width="stretch")


inputs: dict[str, SectionInput] = {}
pending_drawings = []  # (where, section, variant), drawn once every section is read
for section in properties.sections():
    with st.expander(section.label, expanded=True):
        if section.help:
            st.caption(section.help)
        chosen = start.get(section.key) or SectionInput(section.variant().key, section.variant().defaults())
        variant = section.variant(chosen.variant)
        if len(section.variants) > 1:
            labels = [v.label for v in section.variants]
            picked = st.radio("Type", labels, index=labels.index(variant.label), horizontal=True,
                              key=f"{gen}.{section.key}.variant")
            variant = section.variants[labels.index(picked)]
        values = variant.defaults()
        if variant.key == chosen.variant:
            values.update(chosen.values)
        simple = [p for p in variant.properties if p.kind not in ("monthly", "points", "hourly")]
        point_props = [p for p in variant.properties if p.kind == "points"]
        hourly_props = [p for p in variant.properties if p.kind == "hourly"]
        monthly = [p for p in variant.properties if p.kind == "monthly"]
        # wide inputs (tables, hourly files) get their drawing below instead of beside them
        has_drawing = (section.key, variant.key) in plots.DRAWINGS and not monthly and not hourly_props
        form_col, drawing_col = st.columns([2, 1]) if has_drawing else (st.container(), None)
        with form_col:
            preset_pickers(variant, f"{gen}.{section.key}.{variant.key}")
            for prop in hourly_props:
                values[prop.key] = hourly_input(prop, values[prop.key], f"{gen}.{section.key}.{variant.key}.{prop.key}")
            for prop in point_props:
                values[prop.key] = points_input(prop, values[prop.key], f"{gen}.{section.key}.{variant.key}.{prop.key}")
            cols = st.columns(2 if has_drawing else 3)
            for i, prop in enumerate(simple):
                with cols[i % len(cols)]:
                    values[prop.key] = widget(prop, values[prop.key], f"{gen}.{section.key}.{variant.key}.{prop.key}")
            if monthly:
                values.update(monthly_table(monthly, values, f"{gen}.{section.key}.{variant.key}.monthly"))
        inputs[section.key] = SectionInput(variant.key, values)
        if not variant.validate(values):
            for msg in variant.check_warnings(values):
                st.warning(msg)
        # Drawn later because some drawings use other sections too
        # (the borehole picture needs the radius from "Borefield").
        if has_drawing:
            pending_drawings.append((drawing_col, section.key, variant.key))
        elif (section.key, variant.key) in plots.DRAWINGS:
            pending_drawings.append((st.container(), section.key, variant.key))

errors = model.validate(inputs)
for target, section_key, variant_key in pending_drawings:
    if section_key in errors or "borefield" in errors:
        continue
    with target:
        show(plots.DRAWINGS[(section_key, variant_key)][1](inputs))

with save_slot:
    st.download_button("Save project", model.to_json(inputs, name).encode(),
                       f"{name.strip() or 'ghetool-project'}.json", "application/json", width="stretch")

for msgs in errors.values():
    for msg in msgs:
        st.error(msg)


# ---------------------------------------------------------------- results

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


current_json = model.to_json(inputs)
mode_check = inputs["calculation"].variant == "check"
if st.button("Check temperatures" if mode_check else "Size borefield", type="primary", disabled=bool(errors)):
    with st.spinner("Calculating..."):
        try:
            cached_size(current_json)
            st.session_state.result_json = current_json
        except Exception as exc:  # show GHEtool errors to the user instead of crashing
            st.session_state.pop("result_json", None)
            st.error(f"Calculation failed: {exc}")

if "result_json" in st.session_state:
    sized_json = st.session_state.result_json
    sized_inputs = model.from_json(sized_json)[1]
    result = cached_size(sized_json)
    limits = sized_inputs["limits"].values
    key = analysis.key_results(result, sized_inputs)

    st.subheader("Results")
    if sized_json != current_json:
        st.info("The inputs changed since this result was calculated. Click the button above to update it.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Borehole length" if result.sizing_method == "check" else "Required borehole length",
              f"{result.borehole_length:.1f} m")
    c2.metric("Total length", f"{result.total_length:,.0f} m", f"{result.number_of_boreholes} boreholes",
              delta_color="off")
    t_lo, t_hi = (round(key.values[k], 1) + 0.0 for k in ("t_min", "t_max"))  # + 0.0 avoids "-0.0"
    c3.metric("Lowest / highest fluid temperature", f"{t_lo:.1f} / {t_hi:.1f} °C")
    if "cost" in key.values:
        c4.metric("Estimated investment", f"€ {key.values['cost']:,.0f}")
    st.caption({"check": "Temperatures for the given length (no sizing).",
                "hourly": "Sized with hourly resolution (L4).",
                "monthly": "Sized on monthly values (L2/L3)."}[result.sizing_method])
    for w in key.warnings:
        st.warning(w)

    tab_names = ["Key results", "Temperatures over time", "Last year", "Yearly min/max", "Energy balance"]
    if result.hourly_temperatures is not None:
        tab_names += ["Hourly, whole period", "Hourly, last year", "Heat map"]
    tab_names += ["g-function", "Table"]
    tabs = dict(zip(tab_names, st.tabs(tab_names)))
    with tabs["Key results"]:
        st.dataframe(pd.DataFrame(key.rows, columns=["", "Value", "Note"]), hide_index=True, width="stretch",
                     height=35 * (len(key.rows) + 1) + 3)
    with tabs["Temperatures over time"]:
        st.altair_chart(plots.temperature_chart(result.temperatures, limits), width="stretch")
    with tabs["Last year"]:
        st.altair_chart(plots.last_year_chart(result.temperatures, limits), width="stretch")
        if "Into borefield (peak extraction)" in result.temperatures:
            st.caption("Into borefield = supply from the heat pump; out of borefield = return to the heat pump.")
    with tabs["Yearly min/max"]:
        st.altair_chart(plots.yearly_extremes_chart(analysis.yearly_extremes(result), limits), width="stretch")
    with tabs["Energy balance"]:
        st.altair_chart(plots.energy_balance_chart(analysis.monthly_ground_energy(result)), width="stretch")
    if result.hourly_temperatures is not None:
        with tabs["Hourly, whole period"]:
            st.altair_chart(plots.hourly_band_chart(result.hourly_temperatures, limits), width="stretch")
        with tabs["Hourly, last year"]:
            st.altair_chart(plots.hourly_last_year_chart(result.hourly_temperatures, limits), width="stretch")
        with tabs["Heat map"]:
            st.altair_chart(plots.heatmap_chart(result.hourly_temperatures), width="stretch")
    with tabs["g-function"]:
        st.altair_chart(plots.gfunction_chart(analysis.gfunction_curve(result)), width="stretch")
    with tabs["Table"]:
        st.dataframe(result.temperatures.round(2), width="stretch")

    d1, d2, d3 = st.columns(3)
    d1.download_button("Download PDF report", report.make_pdf(result, sized_inputs, name),
                       f"{name.strip() or 'ghetool-project'}.pdf", "application/pdf", type="primary")
    d2.download_button("Download monthly temperatures (CSV)", result.temperatures.to_csv().encode(),
                       "temperatures_monthly.csv", "text/csv")
    if result.hourly_temperatures is not None:
        d3.download_button("Download hourly temperatures (CSV)",
                           result.hourly_temperatures.round(3).to_csv().encode(),
                           "temperatures_hourly.csv", "text/csv")

    # ------------------------------------------------------------ further analysis
    st.subheader("Further analysis")

    with st.expander("Sensitivity check: what the borehole length depends on"):
        st.caption("Sizes the field again with one input changed at a time (monthly sizing for speed).")
        if st.button("Run sensitivity check"):
            st.session_state.sensitivity_json = sized_json
        if st.session_state.get("sensitivity_json") == sized_json:
            with st.spinner("Sizing the variations..."):
                sens = cached_sensitivity(sized_json)
            st.altair_chart(plots.tornado_chart(sens), width="stretch")
            st.dataframe(sens[["Input", "Low", "High"]].round(1), hide_index=True)

    with st.expander("Compare variants"):
        st.caption("Keep results side by side, e.g. single vs. double U or different spacings.")
        label_col, button_col = st.columns([3, 1])
        variant_name = label_col.text_input("Name for this result", value=f"Variant {len(st.session_state.get('kept', [])) + 1}")
        if button_col.button("Keep this result", width="stretch"):
            row = {"Variant": variant_name, "Boreholes": result.number_of_boreholes,
                   "Length each [m]": round(result.borehole_length, 1), "Total length [m]": round(result.total_length),
                   "Lowest temp. [°C]": round(key.values["t_min"], 2), "Highest temp. [°C]": round(key.values["t_max"], 2),
                   "Rb [m·K/W]": round(result.borehole_resistance, 3)}
            if "cost" in key.values:
                row["Investment [€]"] = round(key.values["cost"])
            st.session_state.setdefault("kept", []).append(row)
        kept = st.session_state.get("kept", [])
        if kept:
            table = pd.DataFrame(kept)
            st.dataframe(table, hide_index=True, width="stretch")
            ch1, ch2 = st.columns(2)
            with ch1:
                st.altair_chart(plots.comparison_chart(table, "Total length [m]", "Total length [m]"), width="stretch")
            if "Investment [€]" in table:
                with ch2:
                    st.altair_chart(plots.comparison_chart(table, "Investment [€]", "Investment [€]"), width="stretch")
            if st.button("Clear comparison"):
                st.session_state.kept = []
                st.rerun()

    with st.expander("Optimise the layout for a plot"):
        st.caption("Searches rectangular, L, U, box and staggered fields that fit in the plot and meet the "
                   "temperature limits, and lists the ones with the least drilling. Uses GHEtool's optimiser; "
                   "each trial takes a few seconds.")
        with st.form("optimise"):
            o1, o2, o3 = st.columns(3)
            plot_l = o1.number_input("Plot length [m]", 10.0, 1000.0, 70.0, 5.0)
            plot_w = o1.number_input("Plot width [m]", 10.0, 1000.0, 70.0, 5.0)
            b_min = o2.number_input("Minimum spacing [m]", 3.0, 20.0, 5.0, 0.5)
            b_max = o2.number_input("Maximum spacing [m]", 3.0, 20.0, 8.0, 0.5)
            h_min = o3.number_input("Minimum depth [m]", 20.0, 800.0, 50.0, 5.0)
            h_max = o3.number_input("Maximum depth [m]", 20.0, 800.0, 150.0, 5.0)
            trials = st.slider("Number of trials (more finds better fields, but takes longer)", 10, 100, 20, 5)
            go = st.form_submit_button("Find layouts")
        if go:
            with st.spinner(f"Trying {trials} layouts. This can take a few minutes..."):
                try:
                    st.session_state.optimised = cached_optimisation(sized_json, plot_l, plot_w, b_min, b_max,
                                                                     h_min, h_max, trials)
                except Exception as exc:
                    st.session_state.pop("optimised", None)
                    st.error(f"No layout found: {exc}")
        if "optimised" in st.session_state:
            st.dataframe(st.session_state.optimised.round(1), hide_index=True, width="stretch")

    if sized_inputs["load"].variant == "hourly_building":
        with st.expander("Hybrid system: how much this field can cover"):
            st.caption("Keeps the current borefield and finds the largest share of the hourly demand it can take "
                       "within the temperature limits; the rest comes from a backup boiler or chiller.")
            if st.button("Calculate hybrid share"):
                with st.spinner("Optimising the load split..."):
                    try:
                        st.session_state.hybrid = (sized_json, analysis.hybrid_share(result, sized_inputs))
                    except Exception as exc:
                        st.error(f"Calculation failed: {exc}")
            if st.session_state.get("hybrid", (None,))[0] == sized_json:
                h = st.session_state.hybrid[1]
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Heating covered by the ground", f"{h['heating_share']:.1%}")
                k2.metric("Cooling covered by the ground", f"{h['cooling_share']:.1%}")
                k3.metric("Backup heating needed", f"{h['backup_heating_kw']:,.0f} kW")
                k4.metric("Backup cooling needed", f"{h['backup_cooling_kw']:,.0f} kW")
