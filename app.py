"""Streamlit page. Start with:  streamlit run app.py"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import hashlib

from ghe_web import geometry, hourly, model, plots, properties
from ghe_web.properties import Property, SectionInput
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
    if prop.kind == "float":
        return st.number_input(label, min_value=prop.min, max_value=prop.max, value=float(value),
                               step=prop.step, help=prop.help or None, key=key)
    if prop.kind == "int":
        return int(st.number_input(label, min_value=int(prop.min) if prop.min is not None else None,
                                   max_value=int(prop.max) if prop.max is not None else None,
                                   value=int(value), step=int(prop.step or 1), help=prop.help or None, key=key))
    if prop.kind == "bool":
        return st.checkbox(label, value=bool(value), help=prop.help or None, key=key)
    if prop.kind == "choice":
        return st.selectbox(label, prop.options, index=prop.options.index(value), help=prop.help or None, key=key)
    raise ValueError(prop.kind)


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

if st.button("Size borefield", type="primary", disabled=bool(errors)):
    with st.spinner("Calculating..."):
        try:
            st.session_state.result = (model.size(inputs), inputs["limits"].values, model.to_json(inputs))
        except Exception as exc:  # show GHEtool errors to the user instead of crashing
            st.session_state.pop("result", None)
            st.error(f"Calculation failed: {exc}")

if "result" in st.session_state:
    result, limits, sized_inputs = st.session_state.result
    st.subheader("Results")
    if sized_inputs != model.to_json(inputs):
        st.info("The inputs changed since this result was calculated. Click Size borefield to update it.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Required borehole length", f"{result.borehole_length:.1f} m")
    c2.metric("Total length", f"{result.total_length:.0f} m", f"{result.number_of_boreholes} boreholes",
              delta_color="off")
    c3.metric("Borehole resistance", f"{result.borehole_resistance:.3f} m·K/W")
    st.caption("Sized with hourly resolution (L4)." if result.sizing_method == "hourly"
               else "Sized on monthly values (L2/L3).")
    tab_names = ["Temperatures over time", "Last year", "Table"]
    if result.hourly_temperatures is not None:
        tab_names = ["Hourly, whole period", "Hourly, last year"] + tab_names
    tabs = st.tabs(tab_names)
    if result.hourly_temperatures is not None:
        with tabs[0]:
            st.altair_chart(plots.hourly_band_chart(result.hourly_temperatures, limits), width="stretch")
        with tabs[1]:
            st.altair_chart(plots.hourly_last_year_chart(result.hourly_temperatures, limits), width="stretch")
        tabs = tabs[2:]
    over_time, last_year, table = tabs
    with over_time:
        st.altair_chart(plots.temperature_chart(result.temperatures, limits), width="stretch")
    with last_year:
        st.altair_chart(plots.last_year_chart(result.temperatures, limits), width="stretch")
    with table:
        st.dataframe(result.temperatures.round(2), width="stretch")
    d1, d2 = st.columns(2)
    d1.download_button("Download monthly temperatures (CSV)", result.temperatures.to_csv().encode(),
                       "temperatures_monthly.csv", "text/csv")
    if result.hourly_temperatures is not None:
        d2.download_button("Download hourly temperatures (CSV)",
                           result.hourly_temperatures.round(3).to_csv().encode(),
                           "temperatures_hourly.csv", "text/csv")
