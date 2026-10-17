"""Streamlit page. Start with:  streamlit run app.py"""
import hashlib
import html
import io

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ghe_web import analysis, export, geometry, hourly, model, plots, properties, report
from ghe_web.properties import Property, SectionInput, Variant
from ghe_web.properties.load import MONTHS

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

# Input steps, in page order. A section with an unknown group lands in "More inputs", so new
# sections show up without changes here.
STEPS = {"Site": "① Ground & borefield", "Borehole": "② Borehole & fluid", "Loads": "③ Loads",
         "Design": "④ Limits & costs"}
MORE = "More inputs"
RESULTS = "Results"

# Values the widgets start from: the defaults, or a project the user loaded.
# Widget keys include a generation number, so loading a project rebuilds every widget.
if "project" not in st.session_state:
    st.session_state.project = ("", model.default_inputs())
    st.session_state.generation = 0
project_name, start = st.session_state.project
gen = st.session_state.generation
if st.session_state.pop("goto_results", False):
    st.session_state.step = RESULTS


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
    st.divider()
    calc_slot = st.container()  # the calculate button and a short result, filled at the end

st.title("Borehole heat exchanger sizing")
st.caption("Fill in the four input steps, then press **Size borefield** on the left. Every field has a "
           "question mark with an explanation; the drop-downs fill in typical values.")


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
        return st.toggle(label, help=help_text, key=key, **kw)
    if prop.kind == "choice":
        kw = initial if initial is not None else {"index": prop.options.index(value)}
        return st.selectbox(label, prop.options, help=help_text, key=key, **kw)
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
            st.selectbox(f"🗂 {group.label}", ["Choose to fill in typical values…"] + list(group.options),
                         key=f"{key_prefix}.preset.{group.label}", on_change=apply,
                         help=group.help or "Fills in the fields below with typical values.")


def monthly_table(props: list[Property], values: dict, key: str) -> dict:
    df = pd.DataFrame({f"{p.label} [{p.unit}]": list(values[p.key]) for p in props}, index=MONTHS)
    st.caption("Monthly values. Click a cell to edit; you can paste a column from Excel.")
    edited = st.data_editor(df, key=key, width="stretch", height=35 * 13 + 3)
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
    with st.expander(f"{prop.label}: {len(df)} boreholes (click to edit the coordinates)"):
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
                           "hourly_demand_template.csv", "text/csv", icon=":material/download:",
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
        st.info("Showing an example office profile until you upload your own.", icon=":material/info:")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Heating demand", f"{sum(value['heating']) / 1000:,.0f} MWh/yr")
    c2.metric("Peak heating", f"{max(value['heating']):,.0f} kW")
    c3.metric("Cooling demand", f"{sum(value['cooling']) / 1000:,.0f} MWh/yr")
    c4.metric("Peak cooling", f"{max(value['cooling']):,.0f} kW")
    return value


@st.cache_resource(max_entries=64, show_spinner=False)
def cached_drawing(section_key: str, variant_key: str, project_json: str) -> tuple:
    """Input drawings, cached on the inputs. Matplotlib figures are stored as PNG, charts as they are."""
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
            st.altair_chart(part, width="stretch")


def section_inputs(section) -> tuple[SectionInput, object]:
    """Draws one section and returns its values and where its drawing goes (or None)."""
    with st.container(border=True):
        st.markdown(f"##### {section.label}")
        if section.help:
            st.caption(section.help)
        chosen = start.get(section.key) or SectionInput(section.variant().key, section.variant().defaults())
        variant = section.variant(chosen.variant)
        if len(section.variants) > 1:
            labels = [v.label for v in section.variants]
            picked = st.radio("Input method", labels, index=labels.index(variant.label), horizontal=True,
                              key=f"{gen}.{section.key}.variant")
            variant = section.variants[labels.index(picked)]
        if variant.help:
            st.caption(variant.help)
        values = variant.defaults()
        if variant.key == chosen.variant:
            values.update(chosen.values)
        simple = [p for p in variant.properties if p.kind not in ("monthly", "points", "hourly")]
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
        problems = variant.validate(values)
        for msg in problems:
            st.error(msg, icon=":material/error:")
        if not problems:
            for msg in variant.check_warnings(values):
                st.warning(msg, icon=":material/warning:")
        target = drawing_col if side else (st.container() if has_drawing else None)
    return SectionInput(variant.key, values), target


grouped: dict[str, list] = {}
for section in properties.sections():
    grouped.setdefault(STEPS.get(section.group, MORE), []).append(section)
step_names = [s for s in list(STEPS.values()) + [MORE] if s in grouped] + [RESULTS]
step_tabs = dict(zip(step_names, st.tabs(step_names, key="step", on_change="rerun")))

inputs: dict[str, SectionInput] = {}
section_step: dict[str, str] = {}
pending_drawings = []  # (where, section, variant), drawn once every section is read
for step, sections in grouped.items():
    with step_tabs[step]:
        for section in sections:
            inputs[section.key], target = section_inputs(section)
            section_step[section.key] = step
            # Drawn later because some drawings use other sections too
            # (the borehole picture needs the radius from "Borefield").
            if target is not None:
                pending_drawings.append((target, section.key, inputs[section.key].variant))

errors = model.validate(inputs)
current_json = model.to_json(inputs)
for target, section_key, variant_key in pending_drawings:
    if section_key in errors or "borefield" in errors:
        continue
    with target:
        show_drawing(cached_drawing(section_key, variant_key, current_json))

with save_slot:
    st.download_button("Save project", model.to_json(inputs, name).encode(),
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


mode_check = inputs["calculation"].variant == "check"
action = "Check temperatures" if mode_check else "Size borefield"


def calculate() -> None:
    with st.spinner("Calculating... hourly sizing can take up to a minute."):
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
    st.header("Calculate")
    if errors:
        st.error(f"{sum(len(m) for m in errors.values())} input(s) need attention:\n\n" + "\n".join(
            f"- {section_step.get(k, '')}: {properties.get(k).label}" for k in errors), icon=":material/error:")
    if st.button(action, type="primary", disabled=bool(errors), width="stretch", icon=":material/calculate:"):
        calculate()
    if "calc_error" in st.session_state:
        st.error(f"Calculation failed: {st.session_state.calc_error}")
    if "result_json" in st.session_state:
        res = cached_size(st.session_state.result_json)
        st.metric("Borehole length" if res.sizing_method == "check" else "Required length",
                  f"{res.borehole_length:.1f} m", f"{res.number_of_boreholes} boreholes, {res.total_length:,.0f} m total",
                  delta_color="off", delta_arrow="off")
        if st.session_state.result_json != current_json:
            st.warning("Inputs changed since the last calculation.", icon=":material/update:")
        else:
            st.caption("See the **Results** tab for details.")


# ---------------------------------------------------------------- results

def key_table(rows: list[tuple[str, str, str]]) -> None:
    """A compact two-column table: item with its note underneath, and the value."""
    body = "".join(
        f"<tr><td>{html.escape(label)}<div class='note'>{html.escape(note)}</div></td>"
        f"<td class='val'>{html.escape(value)}</td></tr>" for label, value, note in rows)
    st.markdown(f"<table class='keys'>{body}</table>", unsafe_allow_html=True)


def extra_tables(sized_json: str) -> dict[str, pd.DataFrame]:
    """Analysis the user ran for this result, so the export contains it too."""
    extra = {}
    if st.session_state.get("sensitivity_json") == sized_json:
        sens = cached_sensitivity(sized_json)
        extra["Sensitivity"] = sens.rename(columns={"Low": "Input lower [m]", "High": "Input higher [m]",
                                                    "Base": "Base [m]", "Spread": "Spread [m]"})
    if st.session_state.get("kept"):
        extra["Variant comparison"] = pd.DataFrame(st.session_state.kept)
    if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
        extra["Layout optimisation"] = st.session_state.optimised
    return extra


def view_overview(result, key, limits) -> None:
    if result.hourly_temperatures is not None:  # the hourly result is what the sizing used
        st.altair_chart(plots.hourly_band_chart(result.hourly_temperatures, limits), width="stretch")
        st.caption("Daily range of the hourly average fluid temperature. Dashed: your limits.")
    else:
        st.altair_chart(plots.temperature_chart(result.temperatures, limits), width="stretch")
        st.caption("Blue: coldest fluid (heating peaks). Red: warmest fluid (cooling peaks). Dashed: your limits. "
                   "Black dots: the lowest and highest value.")
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


def view_temperatures(result, limits) -> None:
    choice = st.segmented_control("Chart", ["Over the years", "Last year", "Yearly min/max", "Table"],
                                  default="Over the years", required=True, key="temp_view")
    if choice == "Over the years":
        st.altair_chart(plots.temperature_chart(result.temperatures, limits), width="stretch")
    elif choice == "Last year":
        st.altair_chart(plots.last_year_chart(result.temperatures, limits), width="stretch")
        if "Into borefield (peak extraction)" in result.temperatures:
            st.caption("Into borefield = supply from the heat pump; out of borefield = return to the heat pump.")
    elif choice == "Yearly min/max":
        st.altair_chart(plots.yearly_extremes_chart(analysis.yearly_extremes(result), limits), width="stretch")
        st.caption("If the lowest temperature keeps falling (or the highest keeps rising) every year, the ground "
                   "is out of balance. A longer simulation period shows whether it levels off.")
    else:
        st.dataframe(export.monthly_temperatures(result).round(2), hide_index=True, width="stretch", height=420)


def view_energy(result, key) -> None:
    energy = analysis.monthly_ground_energy(result)
    st.altair_chart(plots.energy_balance_chart(energy), width="stretch")
    st.caption("Energy taken from (heating) and put into (cooling) the ground, after heat pump efficiency.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Taken from the ground", f"{key.values['extraction_mwh']:,.0f} MWh/yr")
    c2.metric("Put into the ground", f"{key.values['injection_mwh']:,.0f} MWh/yr")
    c3.metric("Imbalance", f"{key.values['imbalance_mwh']:+,.0f} MWh/yr")


def view_hourly(result, limits) -> None:
    choice = st.segmented_control("Chart", ["Daily range", "Last year", "Heat map"], default="Daily range",
                                  required=True, key="hourly_view")
    if choice == "Daily range":
        st.altair_chart(plots.hourly_band_chart(result.hourly_temperatures, limits), width="stretch")
    elif choice == "Last year":
        st.altair_chart(plots.hourly_last_year_chart(result.hourly_temperatures, limits), width="stretch")
        st.caption("The band spans the lowest and highest fluid temperature of every 3 hours, so all peaks are "
                   "visible.")
    else:
        st.altair_chart(plots.heatmap_chart(result.hourly_temperatures), width="stretch")
        st.caption("Each cell is one hour of the last year. Blue is cold, red is warm.")


def view_analysis(result, key, sized_json, sized_inputs) -> None:
    with st.expander("Sensitivity check: what the borehole length depends on", icon=":material/tune:"):
        st.caption("Sizes the field again with one input changed at a time (monthly sizing for speed). "
                   "The longest bars are the inputs worth measuring carefully, e.g. with a thermal response test.")
        if st.button("Run sensitivity check"):
            st.session_state.sensitivity_json = sized_json
        if st.session_state.get("sensitivity_json") == sized_json:
            with st.spinner("Sizing the variations..."):
                sens = cached_sensitivity(sized_json)
            st.altair_chart(plots.tornado_chart(sens), width="stretch")
            base = float(sens["Base"].iloc[0])
            table = sens[["Input", "Low", "High"]].copy()
            table["Change, lower [%]"] = (table["Low"] / base - 1) * 100
            table["Change, higher [%]"] = (table["High"] / base - 1) * 100
            st.dataframe(table.round(1).rename(columns={"Low": "Length, input lower [m]",
                                                        "High": "Length, input higher [m]"}), hide_index=True)
            if result.sizing_method != "monthly":
                st.caption(f"The variations use monthly sizing, which gives {base:.1f} m for these inputs "
                           f"(the result above: {result.borehole_length:.1f} m). Read the changes in percent.")

    with st.expander("Compare variants", icon=":material/compare_arrows:"):
        st.caption("Keep this result, change the inputs, size again and keep that one too. "
                   "The comparison stays until you close the page and is part of the Excel export.")
        label_col, button_col = st.columns([3, 1], vertical_alignment="bottom")
        variant_name = label_col.text_input("Name for this result",
                                            value=f"Variant {len(st.session_state.get('kept', [])) + 1}")
        if button_col.button("Keep this result", width="stretch", icon=":material/push_pin:"):
            row = {"Variant": variant_name, "Boreholes": result.number_of_boreholes,
                   "Length each [m]": round(result.borehole_length, 1), "Total length [m]": round(result.total_length),
                   "Lowest temp. [°C]": round(key.values["t_min"], 2),
                   "Highest temp. [°C]": round(key.values["t_max"], 2),
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

    with st.expander("Optimise the layout for a plot", icon=":material/grid_view:"):
        st.caption("Searches rectangular, L, U, box and staggered fields that fit in the plot and meet the "
                   "temperature limits, and lists the ones with the least drilling. Each trial takes a few seconds.")
        with st.form("optimise"):
            o1, o2, o3 = st.columns(3)
            plot_l = o1.number_input("Plot length [m]", 10.0, 1000.0, 70.0, 5.0)
            plot_w = o1.number_input("Plot width [m]", 10.0, 1000.0, 70.0, 5.0)
            b_min = o2.number_input("Minimum spacing [m]", 3.0, 20.0, 5.0, 0.5)
            b_max = o2.number_input("Maximum spacing [m]", 3.0, 20.0, 8.0, 0.5)
            h_min = o3.number_input("Minimum depth [m]", 20.0, 800.0, 50.0, 5.0)
            h_max = o3.number_input("Maximum depth [m]", 20.0, 800.0, 150.0, 5.0)
            trials = st.slider("Number of trials (more finds better fields, but takes longer)", 10, 100, 20, 5)
            go = st.form_submit_button("Find layouts", icon=":material/search:")
        if go:
            with st.spinner(f"Trying {trials} layouts. This takes about {trials * 5 // 60 + 1} minute(s)..."):
                try:
                    st.session_state.optimised = cached_optimisation(sized_json, plot_l, plot_w, b_min, b_max,
                                                                     h_min, h_max, trials)
                    st.session_state.optimised_json = sized_json
                except Exception as exc:
                    st.session_state.pop("optimised", None)
                    st.error(f"No layout found: {exc}")
        if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
            st.dataframe(st.session_state.optimised.round(1), hide_index=True, width="stretch")

    if sized_inputs["load"].variant == "hourly_building":
        with st.expander("Hybrid system: how much this field can cover", icon=":material/call_split:"):
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

    with st.expander("g-function (for specialists)", icon=":material/show_chart:"):
        st.caption("The dimensionless step response of the field. Its rise at large times shows how strongly the "
                   "boreholes influence each other.")
        st.altair_chart(plots.gfunction_chart(analysis.gfunction_curve(result)), width="stretch")


def view_export(result, sized_inputs, sized_json) -> None:
    stem = name.strip() or "ghetool-project"
    extra = extra_tables(sized_json)
    included = ", ".join(extra) if extra else "none yet; run them under Further analysis to include them"
    st.markdown("Files are made when you click, so the page stays fast.")
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown("**Excel workbook**")
        st.caption("Summary, inputs, monthly and yearly temperatures, ground energy, hourly results and your "
                   f"further analysis (included: {included}).")
        st.download_button("Download Excel (.xlsx)", lambda: export.excel_workbook(result, sized_inputs, name, extra),
                           f"{stem}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", icon=":material/table_view:", on_click="ignore")
    with c2, st.container(border=True):
        st.markdown("**PDF report**")
        st.caption("Inputs, drawings, key results and the main charts, ready to send.")
        st.download_button("Download PDF", lambda: report.make_pdf(result, sized_inputs, name), f"{stem}.pdf",
                           "application/pdf", type="primary", icon=":material/picture_as_pdf:", on_click="ignore")
    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        st.markdown("**Everything in one zip**")
        st.caption("Excel workbook, PDF report and the project file, for archiving a design.")
        st.download_button("Download zip", lambda: export.zip_bundle(result, sized_inputs, name, extra),
                           f"{stem}.zip", "application/zip", icon=":material/folder_zip:", on_click="ignore")
    with c4, st.container(border=True):
        st.markdown("**CSV files**")
        st.caption("Plain tables for other tools.")
        st.download_button("Monthly temperatures (CSV)",
                           lambda: export.monthly_temperatures(result).to_csv(index=False).encode(),
                           f"{stem}_monthly.csv", "text/csv", icon=":material/download:", on_click="ignore")
        if result.hourly_temperatures is not None:
            st.download_button("Hourly temperatures (CSV)",
                               lambda: result.hourly_temperatures.round(3).to_csv().encode(),
                               f"{stem}_hourly.csv", "text/csv", icon=":material/download:", on_click="ignore")


with step_tabs[RESULTS]:
    if "result_json" not in st.session_state:
        st.info(f"No result yet. Check the inputs in the steps above, then press **{action}**.",
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
            st.warning(f"The inputs changed since this result was calculated. Press **{action}** to update it.",
                       icon=":material/update:")
        if result.sizing_method == "check":
            if key.values.get("passes"):
                st.success(f"The given length of {result.borehole_length:.0f} m keeps the fluid within the limits.",
                           icon=":material/check_circle:")
            else:
                st.error(f"The given length of {result.borehole_length:.0f} m does not keep the fluid within the "
                         "limits.", icon=":material/cancel:")
        else:
            st.success(f"{result.number_of_boreholes} boreholes of {result.borehole_length:.1f} m keep the fluid "
                       f"between {limits['T_min']:g} and {limits['T_max']:g} °C for "
                       f"{sized_inputs['load'].values['simulation_period']} years "
                       f"({result.sizing_method} sizing).",
                       icon=":material/check_circle:")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Borehole length" if result.sizing_method == "check" else "Required borehole length",
                  f"{result.borehole_length:.1f} m")
        c2.metric("Total length", f"{result.total_length:,.0f} m", f"{result.number_of_boreholes} boreholes",
                  delta_color="off", delta_arrow="off")
        t_lo, t_hi = (round(key.values[k], 1) + 0.0 for k in ("t_min", "t_max"))  # + 0.0 avoids "-0.0"
        for col, label, temp, margin in ((c3, "Lowest fluid temperature", t_lo, key.values["margin_cold"]),
                                         (c4, "Highest fluid temperature", t_hi, key.values["margin_warm"])):
            if abs(margin) < 0.05:  # sizing stops within a few hundredths of a kelvin of the limit
                col.metric(label, f"{temp:.1f} °C", "at the limit", delta_color="off", delta_arrow="off")
            else:
                col.metric(label, f"{temp:.1f} °C", f"{margin:+.1f} K margin" if margin > 0 else
                           f"{-margin:.1f} K beyond the limit", delta_color="normal" if margin > 0 else "inverse")
        if "cost" in key.values:
            c5.metric("Estimated investment", f"€ {key.values['cost']:,.0f}",
                      f"€ {key.values['cost'] / result.total_length:.0f}/m", delta_color="off", delta_arrow="off")
        for w in key.warnings:
            st.warning(w, icon=":material/warning:")

        views = ["Overview", "Temperatures", "Energy"]
        if result.hourly_temperatures is not None:
            views.append("Hourly")
        views += ["Further analysis", "Export"]
        # Only the chosen view is drawn, so large hourly charts are not sent to the browser on every click.
        view = st.segmented_control("View", views, default="Overview", required=True, key="result_view",
                                    label_visibility="collapsed")
        if view == "Overview":
            view_overview(result, key, limits)
        elif view == "Temperatures":
            view_temperatures(result, limits)
        elif view == "Energy":
            view_energy(result, key)
        elif view == "Hourly":
            view_hourly(result, limits)
        elif view == "Further analysis":
            view_analysis(result, key, sized_json, sized_inputs)
        else:
            view_export(result, sized_inputs, sized_json)
