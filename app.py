"""Streamlit page. Start with:  streamlit run app.py"""
import altair as alt
import pandas as pd
import streamlit as st

from ghe_web import model, properties
from ghe_web.properties import Property, SectionInput
from ghe_web.properties.load import MONTHS

st.set_page_config(page_title="GHEtool Web", layout="wide")
st.title("Borehole heat exchanger sizing")


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
    edited = st.data_editor(df, key=key, use_container_width=True)
    return {p.key: [float(x) for x in edited.iloc[:, i]] for i, p in enumerate(props)}


def temperature_chart(temps: pd.DataFrame, limits: dict) -> alt.Chart:
    # Altair treats [ ] in field names specially, so units go in titles, not column names.
    data = temps.reset_index().melt("Years", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line().encode(
        x=alt.X("Years:Q", title="Time [years]"),
        y=alt.Y("Temperature:Q", title="Temperature [°C]"),
        color=alt.Color("Series:N", legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Series", alt.Tooltip("Years:Q", format=".2f"), alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    bounds = pd.DataFrame({"Temperature": [limits["T_min"], limits["T_max"]]})
    rules = alt.Chart(bounds).mark_rule(strokeDash=[6, 4], color="gray").encode(y="Temperature:Q")
    return (lines + rules).properties(height=380, title="Fluid temperatures over the simulation period")


inputs: dict[str, SectionInput] = {}
for section in properties.sections():
    with st.expander(section.label, expanded=True):
        if section.help:
            st.caption(section.help)
        variant = section.variants[0]
        if len(section.variants) > 1:
            labels = {v.label: v for v in section.variants}
            variant = labels[st.radio("Type", list(labels), horizontal=True, key=f"{section.key}.variant")]
        values = variant.defaults()
        simple = [p for p in variant.properties if p.kind != "monthly"]
        monthly = [p for p in variant.properties if p.kind == "monthly"]
        cols = st.columns(3)
        for i, prop in enumerate(simple):
            with cols[i % 3]:
                values[prop.key] = widget(prop, values[prop.key], f"{section.key}.{variant.key}.{prop.key}")
        if monthly:
            values.update(monthly_table(monthly, values, f"{section.key}.{variant.key}.monthly"))
        inputs[section.key] = SectionInput(variant.key, values)

errors = model.validate(inputs)
for msgs in errors.values():
    for msg in msgs:
        st.error(msg)

if st.button("Size borefield", type="primary", disabled=bool(errors)):
    with st.spinner("Calculating..."):
        try:
            result = model.size(inputs)
        except Exception as exc:  # show GHEtool errors to the user instead of crashing
            st.error(f"Calculation failed: {exc}")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Required borehole length", f"{result.borehole_length:.1f} m")
            c2.metric("Total length", f"{result.total_length:.0f} m", f"{result.number_of_boreholes} boreholes",
                      delta_color="off")
            c3.metric("Borehole resistance", f"{result.borehole_resistance:.3f} m·K/W")
            st.altair_chart(temperature_chart(result.temperatures, inputs["limits"].values), use_container_width=True)
            st.download_button("Download temperatures (CSV)", result.temperatures.to_csv().encode(),
                               "temperatures.csv", "text/csv")
