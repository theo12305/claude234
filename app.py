"""Streamlit page. Start with:  streamlit run app.py"""
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ghe_web import model, plots, properties
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


def show(drawing):
    if isinstance(drawing, plt.Figure):
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
        simple = [p for p in variant.properties if p.kind != "monthly"]
        monthly = [p for p in variant.properties if p.kind == "monthly"]
        has_drawing = (section.key, variant.key) in plots.DRAWINGS and not monthly
        form_col, drawing_col = st.columns([2, 1]) if has_drawing else (st.container(), None)
        with form_col:
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
    over_time, last_year, table = st.tabs(["Temperatures over time", "Last year", "Table"])
    with over_time:
        st.altair_chart(plots.temperature_chart(result.temperatures, limits), width="stretch")
    with last_year:
        st.altair_chart(plots.last_year_chart(result.temperatures, limits), width="stretch")
    with table:
        st.dataframe(result.temperatures.round(2), width="stretch")
    st.download_button("Download temperatures (CSV)", result.temperatures.to_csv().encode(),
                       "temperatures.csv", "text/csv")
