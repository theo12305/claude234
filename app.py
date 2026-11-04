"""Streamlit page. Start with:  streamlit run app.py"""
import hashlib
import html
import io
import math
import pathlib
import sys
import textwrap

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

from ghe_web import analysis, checks, export, geometry, guidance, hourly, i18n, model, plots, properties, report, share, ui
from ghe_web.i18n import fmt, t
from ghe_web.siteplan import page as siteplan_page
from ghe_web.strata import page as strata_page
from ghe_web.properties import Property, SectionInput, Variant
from ghe_web.wells import page as wells_page
from ghe_web import results
from ghe_web.results import common as results_common, registry as results_registry, sheet as results_sheet, \
    summary as results_summary
from ghe_web.results.cache import cached_size

st.set_page_config(page_title="GHEtool & Co.", page_icon="🌍", layout="wide")
ui.inject_css()
st.html("""<style>
table.keys {width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0;}
table.keys td {border: none; border-bottom: 1px solid rgba(128,128,128,0.18); padding: 6px 4px; vertical-align: top;}
table.keys tr:last-child td {border-bottom: none;}
table.keys td.val {text-align: right; font-weight: 600; white-space: nowrap; padding-left: 12px;}
table.keys .note {font-size: 0.78rem; opacity: 0.65; line-height: 1.25;}
@media (max-width: 640px) {
  table.keys td:first-child {width: 55%;}
  table.keys td.val {white-space: normal; padding-left: 8px;}
}
</style>""")

# ---------------------------------------------------------------- app bar, language first (everything below follows it)

if "pending_language" in st.session_state:  # set by opening a project file
    st.session_state.language = st.session_state.pop("pending_language")
if "pending_mode" in st.session_state:
    st.session_state.ui_mode = st.session_state.pop("pending_mode")
# A bar at the top with the name, Simple/Expert, the language and the menu. No sidebar: phones hide it.
appbar = st.container(key="appbar", horizontal=True, vertical_alignment="center", gap="small")
with appbar:
    brand_slot = st.empty()
    st.space("stretch")
    mode_slot = st.empty()
    lang = st.segmented_control("Language · Sprache", list(i18n.LANGUAGES), format_func=lambda c: c.upper(),
                                default=i18n.DEFAULT, required=True, key="language", label_visibility="collapsed")
    menu = st.popover("", icon=":material/menu:", help="Menu")
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
MODES = {"simple": "Simple", "expert": "Expert"}
with mode_slot:
    ui_mode = st.segmented_control(t("Mode"), list(MODES), format_func=lambda k: t(MODES[k]), default="simple",
                                   required=True, key="ui_mode", label_visibility="collapsed")


if ui_mode == "expert":  # Expert: denser inputs, so the two modes look different and more fits on the screen
    st.html("""<style>
.stTabs [data-testid="stVerticalBlock"] {gap: .55rem;}
.stTabs [data-testid="stNumberInput"] input {height: 2.1rem; font-size: .9rem;}
.stTabs [data-baseweb="select"] > div {min-height: 2.1rem; font-size: .9rem;}
.stTabs [data-testid="stWidgetLabel"] p {font-size: .82rem;}
.stTabs h5 {font-size: 1rem; padding-bottom: .3rem;}
.stTabs div[data-testid="stVerticalBlock"][data-test-scroll-behavior] {padding: 10px 14px;}
.rangebar {margin: -4px 0 6px;} .rangebar .txt {font-size: .7rem;}
</style>""")


in_language = results_common.in_language


def chart(c, width="stretch") -> None:
    ui.show_chart(c, width)


# Input steps, in page order. A section with an unknown group lands in "More inputs", so new
# sections show up without changes here. The tab labels follow the language; the ids stay the same.
STEP_LABELS = {"site_plan": "⓪ Site plan", "Site": "① Ground & borefield", "Borehole": "② Borehole & fluid",
               "Loads": "③ Loads", "Design": "④ Limits & calculation", "more": "More inputs",
               "check": "⑤ Design check", "results": "📊 Results", "analysis": "🔬 Further analysis"}
# The same steps for groundwater wells (open loop)
WELL_STEP_LABELS = {"site_plan": "⓪ Site plan", "Site": "① Ground & aquifer", "Borehole": "② Wells",
                    "Loads": "③ Loads", "Design": "④ Limits & calculation", "more": "More inputs",
                    "results": "📊 Results"}

# Simple mode: the borehole, fluid and limits are part of the Loads step, which becomes step 2
SIMPLE_STEP_LABELS = {"Loads": "② Loads", "check": "③ Design check"}
# Input methods for specialists: listed in Expert only (and in Simple while a project uses them)
EXPERT_ONLY = {("load", "monthly"), ("load", "hourly_building"), ("heat_pump", "curve"), ("pipe", "coaxial"),
               ("pipe", "constant_rb")}

# Values the widgets start from: the defaults, or a project the user loaded.
# Widget keys include a generation number, so loading a project rebuilds every widget.
if "project" not in st.session_state:
    st.session_state.project = ("", model.default_inputs())
    st.session_state.generation = 0
if share.PARAM in st.query_params:  # opened from a share link: load its project once, then drop it from the address
    packed = st.query_params[share.PARAM]
    del st.query_params[share.PARAM]
    try:
        text = share.decode(packed)
        st.session_state.project = model.from_json(text)
    except Exception:
        st.session_state.link_error = True
    else:
        saved = model.saved_language(text)
        if saved in i18n.LANGUAGES:
            st.session_state.pending_language = saved
        if model.saved_setting(text, "mode") in ("simple", "expert"):
            st.session_state.pending_mode = model.saved_setting(text, "mode")
        siteplan_page.set_address(model.saved_setting(text, "address") or "")
        results_registry.load_plugin_data(model.saved_plugins(text))
        st.session_state.generation += 1
        st.session_state.opened_link = True
    st.rerun()
project_name, start = st.session_state.project
gen = st.session_state.generation
# The heat source decides the sections and tabs. Its radio is drawn further down, so read its value here.
system = st.session_state.get(f"{gen}.system.variant_key", model.system(start))
LABELS = WELL_STEP_LABELS if system == "open" else STEP_LABELS
SIMPLE = ui_mode != "expert"
if SIMPLE:  # three input steps: the borehole, fluid and limits come with typical values under Loads
    LABELS = {**LABELS, **SIMPLE_STEP_LABELS}
STEPS = {k: t(v) for k, v in LABELS.items()}
if SIMPLE:
    STEPS["Borehole"] = STEPS["Design"] = STEPS["Loads"]
SITE_PLAN, MORE, RESULTS = STEPS["site_plan"], STEPS["more"], STEPS["results"]
CHECK, ANALYSIS = STEPS.get("check"), STEPS.get("analysis")  # borehole heat exchangers only
if st.session_state.pop("goto_results", False):
    st.session_state.step = RESULTS
if "goto_step" in st.session_state:
    st.session_state.step = STEPS[st.session_state.pop("goto_step")]
if st.session_state.get("step") not in (None, *STEPS.values()):  # language or heat source changed: same tab, new label
    for code in i18n.LANGUAGES:
        with i18n.using(code):
            match = [k for labels in (STEP_LABELS, WELL_STEP_LABELS, SIMPLE_STEP_LABELS) for k, v in labels.items()
                     if t(v) == st.session_state.step]
        if match:
            st.session_state.step = STEPS[match[0]]
            break
    else:
        del st.session_state.step


# ---------------------------------------------------------------- menu: project, save / load, help

with menu:
    st.markdown(t("**Project**"))
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
            if model.saved_setting(text, "mode") in ("simple", "expert"):
                st.session_state.pending_mode = model.saved_setting(text, "mode")
            siteplan_page.set_address(model.saved_setting(text, "address") or "")
            results_registry.load_plugin_data(model.saved_plugins(text))
            st.session_state.generation += 1
            st.session_state.welcomed = True
            st.rerun()
    save_slot = st.empty()  # filled after the inputs are read
    share_slot = st.container()
    st.caption(t("Projects are saved as a file on your computer, including the language. Nothing is stored on "
                 "the server."))
    st.divider()
    st.markdown(t("**Help**"))
    with st.expander(t("How to use this tool"), icon=":material/help:"):
        if system == "open":
            st.markdown(t(
                "1. **⓪ Site plan** (optional): find the parcel.\n"
                "2. **① Ground & aquifer**: choose groundwater wells as heat source, the ground temperature (or predicted "
                "layers), the aquifer and the water analysis.\n"
                "3. **② Wells**: drilling diameter, well losses, and whether to size the wells or check given ones.\n"
                "4. **③ Loads**: the heat taken from and put into the groundwater, or the building demand.\n"
                "5. **④ Limits & calculation**: temperature spread and the limits of the water authority.\n"
                "6. Press **Size the wells** in the bar at the bottom. The **📊 Results** tab shows the flow, wells, water levels, "
                "temperatures, the site map, the well construction and the downloads.\n\n"
                "The well hydraulics (Thiem, Dupuit-Jacob, Sichardt) and the thermal model (flow paths of the injected "
                "water and a planar plume) are written for this tool; GHEtool has no open-loop model."))
        else:
            st.markdown(t(
                "1. **⓪ Site plan** (optional): find the parcel and place as many boreholes as fit.\n"
                "2. **① Ground & borefield**: ground properties (or predicted layers) and the borefield layout.\n"
                "3. **② Borehole & fluid**: borehole heat exchanger, heat transfer fluid and flow rate.\n"
                "4. **③ Loads**: the heat extracted from and injected into the ground, or the building demand with the "
                "heat pump efficiency.\n"
                "5. **④ Limits & calculation**: the allowed fluid temperatures, and whether to size the length or check a "
                "given one.\n"
                "6. Press **Size borefield** in the bar at the bottom. The **📊 Results** tab shows key figures, charts, further "
                "analysis and the PDF report and Excel export.\n\n"
                "Save the project in the menu ☰ to continue later. Calculations use the open-source "
                "[GHEtool](https://github.com/wouterpeere/GHEtool)."))
    st.caption(t("🌙 Dark mode: menu **⋮** at the top right > **Settings** > theme **Dark**."))
    st.caption(t("Simple / Expert: the switch next to the language. Simple shows the main fields and puts the others "
                 "under \"More options\"; nothing is left out of the calculation."))
    if system == "open":
        wells_page.sources_button("menu")
    if st.button(t("Change the heat source"), icon=":material/swap_horiz:", width="stretch",
                 help=t("Opens the start page with the choice between borehole heat exchangers and groundwater "
                        "wells. Your inputs stay.")):
        st.session_state.welcomed = False
        st.rerun()

with brand_slot:
    ui.brand(t("Groundwater well sizing") if system == "open" else t("Borehole heat exchanger sizing"))

# ---------------------------------------------------------------- start page: the heat source

def choose_heat_source(choice: str, hit: dict | None = None) -> None:
    """Start with this heat source. Like opening a project, so every widget starts from the stored inputs. With an
    address found on the start page, the site plan opens and loads the parcel there."""
    _, inputs_now = st.session_state.project
    inputs_now = {**inputs_now, "system": SectionInput(choice, {})}
    if st.session_state.get("ui_mode", "simple") != "expert" and inputs_now["load"].variant == "monthly":
        # Simple asks about the building (heat per year, peak, cooling), not the monthly ground load
        building = properties.get("load").variant("annual_building")
        inputs_now["load"] = SectionInput(building.key, building.defaults())
    st.session_state.project = (st.session_state.get(f"{gen}.name", project_name), inputs_now)
    st.session_state.generation += 1
    st.session_state.welcomed = True
    if hit is not None:
        siteplan_page.start_from_address(st.session_state.get("welcome.address", "").strip() or hit["label"], hit)
        st.session_state.goto_step = "site_plan"
    else:
        st.session_state.goto_step = "Site"


def welcome_address() -> dict | None:
    """The optional address on the start page; the place picked from the matches, or None."""
    with st.container(border=True):
        st.markdown("#### 📍 " + t("Where is the site? (optional)"))
        st.caption(t("With an address the site plan opens with the parcel, the buildings and the distances of the "
                     "state, places the boreholes or wells, and the ground layers can be predicted for this place. "
                     "Leave it empty to enter the values yourself."))
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        query = c1.text_input(t("Address"), placeholder=t("e.g. Hauptstraße 5, 52062 Aachen"), key="welcome.address")
        if c2.button(t("Find"), key="welcome.find", width="stretch", icon=":material/search:") and query.strip():
            with st.spinner(t("Searching the address...")):
                st.session_state["welcome.hits"] = siteplan_page.geocode(query.strip())
        hits = st.session_state.get("welcome.hits")
        if hits == []:
            st.warning(t("No address found. Try without the house number, or start without an address and find the "
                         "parcel in step ⓪ Site plan."), icon=":material/warning:")
        if not hits or not query.strip():
            return None
        labels = [h["label"] for h in hits]
        pick = st.selectbox(t("Matching places"), labels, key="welcome.pick") if len(hits) > 1 else labels[0]
        st.success(t("**{place}** – now choose the heat source below.", place=pick), icon=":material/location_on:")
        return hits[labels.index(pick)]


if not st.session_state.get("welcomed", gen > 0):
    with st.container(key="welcome"):
        st.html(f"<div class='welcome'><h2>{html.escape(t('Size a geothermal system in your browser'))}</h2>"
                f"<p class='lead'>{html.escape(t('Free and without login. Your project stays on your device.'))}"
                f"</p></div>")
        hit = welcome_address()
        st.markdown(f"<div style='text-align:center' class='lbl'>{html.escape(t('Which heat source?'))}</div>",
                    unsafe_allow_html=True)
        for col, (key_, (icon, label, text_)) in zip(st.columns(2, gap="medium"), guidance.HEAT_SOURCES.items()):
            with col, st.container(border=True):
                st.html(f"<div class='choice'>{icon}</div>")
                st.markdown(f"#### {t(label)}")
                st.caption(t(text_))
                st.button(t("Start with {what} at this address", what=t(label)) if hit else
                          t("Start with {what}", what=t(label)), key=f"welcome.{key_}", width="stretch",
                          type="primary" if key_ == model.system(start) else "secondary",
                          on_click=choose_heat_source, args=(key_, hit), icon=":material/arrow_forward:")
        st.caption(t("You can switch later in the menu ☰ or under ① in the heat source section. To continue a saved "
                     "project, open it in the menu ☰."))
    st.stop()

if st.session_state.get("step") not in (None, SITE_PLAN, STEPS["Site"]):
    pass  # the intro only on the first steps
elif system == "open":
    st.caption(t("Fill in the input steps, then press **Size the wells** in the bar at the bottom. Every field has a "
                 "question mark with an explanation; the drop-downs fill in typical values."))
else:
    st.caption(t("Fill in the input steps, then press **Size borefield** in the bar at the bottom. Every field has a "
                 "question mark with an explanation; the drop-downs fill in typical values."))
if st.session_state.pop("opened_link", False):
    st.success(t("Opened the project from the link. Hourly demand files are not part of links: upload it again if "
                 "the project uses one."), icon=":material/link:")
if st.session_state.pop("link_error", False):
    st.error(t("This link does not contain a readable project. Ask for a new link or the project file."),
             icon=":material/link_off:")



# The calculate bar: fixed at the bottom of the screen (CSS), filled once the inputs are read.
calc_slot = st.container(key="calcbar", horizontal=True, vertical_alignment="center", gap="small")


# ---------------------------------------------------------------- inputs

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
        ui.range_bar(float(value), rng, prop.min, prop.max, rock)
    now = {k: st.session_state.get(f"{prefix}.{k}", v) for k, v in values.items()}
    note = guidance.side_note(prop.key, float(value), now)
    if note:
        ui.side_note(note)


def field_grid(props: list[Property], values: dict, prefix: str, n_cols: int) -> None:
    # on a phone the columns stack, which would mix up the order (column by column): one column there
    cols = st.columns(1 if ui.is_phone() else n_cols)
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
    for sections that need them before it is read. For wells: the aquifer bottom, from the surface."""
    if system == "open":
        chosen = start.get("aquifer") or SectionInput("unconfined", {})
        variant = st.session_state.get(f"{gen}.aquifer.variant_key", chosen.variant)
        defaults = {**properties.get("aquifer").variant(variant).defaults(),
                    **(chosen.values if variant == chosen.variant else {})}
        return float(st.session_state.get(f"{gen}.aquifer.{variant}.bottom", defaults["bottom"])), 0.0
    chosen = start.get("borefield") or SectionInput("rectangular", {})
    section = properties.get("borefield")
    variant = st.session_state.get(f"{gen}.borefield.variant_key", chosen.variant)
    defaults = {**section.variant(variant).defaults(), **(chosen.values if variant == chosen.variant else {})}
    return (float(st.session_state.get(f"{gen}.borefield.{variant}.H", defaults["H"])),
            float(st.session_state.get(f"{gen}.borefield.{variant}.D", defaults["D"])))


def variant_choices(section, chosen: str) -> list[str]:
    """The input methods listed for a section: all in Expert; in Simple the specialist ones only while in use."""
    current = st.session_state.get(f"{gen}.{section.key}.variant_key", chosen)
    return [v.key for v in section.variants if not SIMPLE or (section.key, v.key) not in EXPERT_ONLY
            or v.key in (chosen, current)]


def hidden_in_simple(section) -> bool:
    """Simple mode leaves out a section with nothing to choose: one input method and no fields (the heat pump
    efficiency with the SCOP/SEER of the building demand)."""
    chosen = start.get(section.key) or SectionInput(section.variant().key, {})
    keys = variant_choices(section, chosen.variant)
    return SIMPLE and len(keys) == 1 and not section.variant(keys[0]).properties


def section_inputs(section) -> tuple[SectionInput, object]:
    """Draws one section and returns its values and where its drawing goes (or None)."""
    with st.container(border=True):
        chosen = start.get(section.key) or SectionInput(section.variant().key, section.variant().defaults())
        variant = section.variant(chosen.variant)
        # descriptions sit behind the question marks, so the page shows the fields only
        about = t(section.help) if section.help else None
        keys = variant_choices(section, variant.key)
        if len(keys) == 1 and section.variant(keys[0]).help:
            about = " ".join(x for x in (about, t(section.variant(keys[0]).help)) if x)
        st.markdown(f"##### {t(section.label)}", help=about)
        if len(keys) > 1:  # the section heading names it, so the drop-down has no label of its own
            shown = section.variant(st.session_state.get(f"{gen}.{section.key}.variant_key", variant.key))
            picked = st.selectbox(t(section.label), keys, index=keys.index(variant.key),
                                  format_func=lambda k: t(section.variant(k).label),
                                  key=f"{gen}.{section.key}.variant_key", label_visibility="collapsed",
                                  help=t(shown.help) if shown.help else None)
            variant = section.variant(picked)
        elif keys[0] != variant.key:
            variant = section.variant(keys[0])
        values = variant.defaults()
        if variant.key == chosen.variant:
            values.update(chosen.values)
        simple = [p for p in variant.properties if p.kind not in ("monthly", "points", "hourly", "layers")
                  and not (SIMPLE and (section.key, p.key) in guidance.SIMPLE_HIDDEN)]
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
            preset_pickers(variant, prefix, values)
            for prop in hourly_props:
                values[prop.key] = hourly_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            for prop in point_props:
                values[prop.key] = points_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            # Simple mode: specialist fields under "More options" (still read and used); Expert: all in line.
            # Simple: fields a drop-down fills in (rock type, pipe, grout, ...) go under "More options" too
            filled = {k for group in variant.presets for option in group.options.values() for k in option}
            basic = [p for p in simple if not SIMPLE or not (guidance.is_advanced(section.key, p.key) or
                                                              p.key in filled)]
            more = [p for p in simple if p not in basic]
            field_grid(basic, values, prefix, (2 if side else 3) if SIMPLE else (3 if side else 4))
            if more:
                with st.expander(t("More options ({n})", n=len(more)), icon=":material/tune:"):
                    st.caption(t("Fields most people leave at their typical value. They are always part of the "
                                 "calculation; switch to Expert at the top to see every field at once."))
                    field_grid(more, values, prefix, 2 if side else 3)
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


def next_step_button(step: str) -> None:
    """At the bottom of each step: go on to the next one. The last input step calculates and opens the results."""
    following = step_names[step_names.index(step) + 1]
    with st.container(horizontal=True, horizontal_alignment="right", key=f"next.{step_names.index(step)}"):
        if following == RESULTS:
            st.button(t("Calculate and show the results"), type="primary", icon=":material/play_arrow:",
                      on_click=lambda: st.session_state.update(calc_requested=True))
        else:
            key_ = next(k for k, v in STEPS.items() if v == following)
            st.button(t("Next: {step}", step=following), icon=":material/arrow_forward:", type="primary",
                      on_click=lambda: st.session_state.update(goto_step=key_))


grouped: dict[str, list] = {}
for section in properties.sections(system):
    grouped.setdefault(STEPS.get(section.group, MORE), []).append(section)
step_names = [SITE_PLAN] + list(dict.fromkeys(s for s in [STEPS[k] for k in ("Site", "Borehole", "Loads", "Design")]
                                              + [MORE] if s in grouped))
# borehole heat exchangers: confirm the design check, then the results, then the further analysis
step_names += [CHECK, RESULTS, ANALYSIS] if CHECK else [RESULTS]
step_tabs = dict(zip(step_names, st.tabs(step_names, default=STEPS["Site"], key="step", on_change="rerun")))

inputs: dict[str, SectionInput] = {}
notes: dict[str, object] = {}
section_step: dict[str, str] = {}
pending_drawings = []  # (where, section, variant), drawn once every section is read
typical_cards = []  # (where, sections): the summary of the typical values in Simple, written once all are read


def read_section(section, step: str) -> None:
    inputs[section.key], target = section_inputs(section)
    section_step[section.key] = step
    # Drawn later because some drawings use other sections too
    # (the borehole picture needs the radius from "Borefield").
    if target is not None:
        pending_drawings.append((target, section.key, inputs[section.key].variant))


def typical_summary(sections) -> str:
    """One line per section: the input method, the drop-down choices and the main values."""
    lines = []
    for section in sections:
        chosen = inputs[section.key]
        variant = section.variant(chosen.variant)
        prefix = f"{gen}.{section.key}.{variant.key}"
        parts = [t(variant.label)] if len(section.variants) > 1 else []
        filled = set()
        for group in variant.presets:
            pick = st.session_state.get(f"{prefix}.preset.{group.label}")
            if pick:
                parts.append(t(pick))
                filled |= {k for k in group.options[pick]}
        for prop in variant.properties:
            if prop.kind in ("float", "int", "choice") and prop.key not in filled and \
                    not guidance.is_advanced(section.key, prop.key) and len(parts) < 5:
                value = chosen.values.get(prop.key)
                if prop.kind == "choice":
                    parts.append(t(str(value)))
                else:
                    parts.append(f"{t(prop.label)} {value:g}" + (f" {t(prop.unit)}" if prop.unit
                                                                                   else ""))
        lines.append(f"**{t(section.label)}:** " + " · ".join(parts))
    return "  \n".join(lines)


for step, sections in grouped.items():
    with step_tabs[step]:
        if step == STEPS["Site"] and "site_plan_done" in st.session_state:
            st.success(t("Borefield set to an irregular field with the {n} positions from the site plan.",
                         n=st.session_state.pop("site_plan_done")), icon=":material/check_circle:")
        if step == STEPS["Borehole"] and "well_plan_done" in st.session_state:
            st.success(t("Wells set from the site plan: {p} production and {i} injection well(s), {d:.0f} m apart, "
                         "{b:.0f} m to the parcel border downstream.", **st.session_state.pop("well_plan_done")),
                       icon=":material/check_circle:")
        # Simple: the calculation method stays asked; the borehole, fluid and limits go in the typical values card
        typical = [x for x in sections if SIMPLE and x.group in ("Borehole", "Design") and x.key != "calculation"]
        for section in [x for x in sections if x not in typical]:
            if hidden_in_simple(section):
                chosen = start.get(section.key)
                key_ = variant_choices(section, chosen.variant if chosen else section.variant().key)[0]
                inputs[section.key] = SectionInput(key_, chosen.values if chosen and chosen.variant == key_
                                                   else section.variant(key_).defaults())
                continue
            read_section(section, step)
        if typical:  # Simple: one card with typical values, opened to change them
            st.markdown("##### " + t("Typical values"), help=t(
                "These inputs start with values that suit most projects. Open the card to change them; Expert at the "
                "top shows them as steps of their own."))
            summary_slot = st.empty()
            with st.expander(t("Change the typical values"), icon=":material/tune:"):
                for section in typical:
                    read_section(section, step)
            typical_cards.append((summary_slot, typical))
        next_step_button(step)

for key, chosen in start.items():  # keep the inputs of the other heat source in the project file
    inputs.setdefault(key, chosen)
errors = model.validate(inputs)
cross = model.cross_warnings(inputs)
for section_key, msgs in cross.items():
    with notes[section_key].container():
        for msg in msgs:
            st.info(msg, icon=":material/info:")


def aquifer_from_layers() -> None:
    """Under Aquifer: the permeable layers below the groundwater in the layer table of Ground, with a button that
    copies their depth, kf and porosity."""
    from ghe_web.wells.aquifer import from_layers
    rows = list((inputs["ground"].values.get("layers") or {}).get("rows") or ())
    chosen = inputs["aquifer"]
    guess = from_layers(rows, chosen.values["water_depth"]) if rows else None
    if guess is None or "aquifer" in cross:
        return
    prefix = f"{gen}.aquifer.{chosen.variant}"
    new = {"bottom": round(guess.bottom, 1), "kf": float(f"{guess.kf:.1e}"), "porosity": round(guess.porosity, 2)}
    if chosen.variant == "confined":
        new["top"] = round(guess.top, 1)
    if all(abs(chosen.values[k] - v) < 1e-9 for k, v in new.items()):
        return
    with notes["aquifer"].container():
        st.info(t("The layer table under Ground has a permeable stretch ({rocks}) from {top:.1f} to {bottom:.1f} m "
                  "below ground, kf about {kf:.1e} m/s (typical values for these rocks).",
                  rocks=", ".join(t(r) for r in guess.rocks), top=guess.top, bottom=guess.bottom, kf=guess.kf),
                icon=":material/layers:")
        st.button(t("Use these values"), key=f"{prefix}.from_layers", icon=":material/download:",
                  on_click=lambda: st.session_state.update({f"{prefix}.{k}": v for k, v in new.items()}))


if system == "open":
    aquifer_from_layers()
current_json = model.to_json(inputs)
for slot, sections in typical_cards:
    with slot.container(border=True):
        st.markdown(typical_summary(sections))
for target, section_key, variant_key in pending_drawings:
    if section_key in errors or "borefield" in errors:
        continue
    with target:  # always visible, in both modes
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
    st.session_state.site_plan_origin = ((x0, y0), values["points"])  # the material list plan draws the buildings
    st.session_state.project = (name, {**inputs, "borefield": SectionInput("custom", values)})
    st.session_state.generation += 1
    st.session_state.goto_step = "Site"
    st.session_state.site_plan_done = len(pts)
    st.rerun()



def use_well_plan(placement, direction: float) -> None:
    """Called from the site plan for groundwater wells: numbers, distance, border distance and flow direction."""
    st.session_state.well_plan = (placement, direction)
    st.rerun()


if "well_plan" in st.session_state:
    placement, direction = st.session_state.pop("well_plan")
    w = inputs["wells"]
    values = {**w.values, "border": float(placement.border_downstream), "orientation": "Injection downstream"}
    if len(placement.production) > 1 or len(placement.injection) > 1:
        spacings = [math.dist(a, b) for group in (placement.production, placement.injection)
                    for a, b in zip(group, group[1:])]
        values["spacing"] = round(min(spacings), 1)
    if w.variant == "check":
        values.update(n_production=len(placement.production), n_injection=len(placement.injection),
                      distance=float(placement.distance))
    else:
        values["max_distance"] = float(placement.distance)
    aquifer_input = inputs["aquifer"]
    st.session_state.project = (name, {**inputs, "wells": SectionInput(w.variant, values),
                                       "aquifer": SectionInput(aquifer_input.variant,
                                                               {**aquifer_input.values, "direction": direction})})
    st.session_state.generation += 1
    st.session_state.goto_step = "Borehole"
    st.session_state.well_plan_done = {"p": len(placement.production), "i": len(placement.injection),
                                       "d": placement.distance, "b": placement.border_downstream}
    st.rerun()


def well_plan_defaults() -> dict:
    """What the site plan starts from for wells: the flow direction, the spacing and the numbers of wells (given, or
    from the last sizing)."""
    w = inputs["wells"].values
    n_p, n_i = w.get("n_production", 1), w.get("n_injection", 1)
    if inputs["wells"].variant == "size" and "result_json" in st.session_state:
        try:
            d = wells_page.cached_design(st.session_state.result_json)
            n_p, n_i = d.n_production, d.n_injection
        except Exception:
            pass
    return {"direction": inputs["aquifer"].values["direction"], "spacing": w["spacing"], "n_production": n_p,
            "n_injection": n_i}


@st.fragment
def site_plan() -> None:
    """The site plan as a fragment: a click on the map or a changed distance redraws only the site plan, not the
    input steps and results. Loading a parcel and using the positions rerun the whole page."""
    if system == "open":
        siteplan_page.page(use_well_plan, well_plan_defaults())
    else:
        siteplan_page.page(use_site_plan)


with step_tabs[SITE_PLAN]:
    # Only drawn while open: the map and the data services are slow.
    if st.session_state.get("step") == SITE_PLAN:
        site_plan()
    next_step_button(SITE_PLAN)

_address, _plugins = siteplan_page.address(), results_registry.plugin_store()


def project_json() -> str:
    """The project file: inputs, name, language, Simple/Expert, the address of the site plan and the settings of
    the result views (read when the download is clicked, so settings changed inside a view are included)."""
    return model.to_json(inputs, name, language=lang, mode=ui_mode, address=_address, plugins=_plugins)


with save_slot:
    st.download_button(t("Save project"), lambda: project_json().encode(),
                       f"{name.strip() or 'ghetool-project'}.json", "application/json", width="stretch",
                       icon=":material/save:", on_click="ignore")
with share_slot, st.expander(t("Share link"), icon=":material/link:"):
    link, dropped = share.link(st.context.url or "", project_json())
    st.markdown(t("**Share this project**"))
    st.caption(t("Anyone with the link opens the site with your inputs filled in. The project is stored in the link "
                 "itself; nothing is saved on the server. Copy it with the button at the right of the box."))
    st.code(link, language=None, wrap_lines=True)
    if dropped:
        st.warning(t("The hourly demand file is not part of the link (too large): send the file separately."),
                   icon=":material/warning:")
    if len(link) > 8000:
        st.caption(t("This link is long ({n:,} characters). Some e-mail programs cut long links; if it does not "
                     "open, send the project file instead.", n=len(link)))


# ---------------------------------------------------------------- calculation

if "result_json" in st.session_state and model.system(model.from_json(st.session_state.result_json)[1]) != system:
    del st.session_state.result_json  # a result of the other heat source

if system == "open":
    def _step_of_section(section_key: str) -> str:
        group = properties.get(section_key).group
        return STEPS[group if group in STEPS and group not in ("site_plan", "results") else "more"]

    def _goto_section(section_key: str) -> None:
        group = properties.get(section_key).group
        st.session_state.goto_step = group if group in STEPS and group not in ("site_plan", "results") else "more"

    wells_page.page(inputs, errors, current_json, name, lang, calc_slot, step_tabs[RESULTS], _step_of_section,
                    _goto_section)
    st.stop()

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


def section_step_key(section_key: str) -> str:
    group = properties.get(section_key).group
    return group if group in STEPS and group not in ("site_plan", "results") else "more"


if st.session_state.pop("calc_requested", False):  # the button at the end of the last input step
    if errors:
        st.session_state.goto_step = section_step_key(next(iter(errors)))
        st.rerun()
    calculate()


def design_checks() -> list[checks.Check]:
    """Input checks, plus the result checks when the current inputs have been calculated."""
    found = checks.input_checks(inputs)
    if not errors and st.session_state.get("result_json") == current_json:
        res = cached_size(current_json)
        found += checks.result_checks(res, inputs, analysis.key_results(res, inputs))
    order = {checks.PROBLEM: 0, checks.WARNING: 1, checks.FINE: 2}
    return sorted(found, key=lambda c: order[c.level])


def open_design_check() -> None:
    st.session_state.goto_step = "check"


check_icons = {checks.PROBLEM: ":red[:material/cancel:]", checks.WARNING: ":orange[:material/warning:]",
               checks.FINE: ":green[:material/check_circle:]"}


def show_design_check(found: list[checks.Check]) -> None:
    st.markdown(t("**Design check: {summary}**", summary=checks.summary(found)))
    ui.caption(t("Every check in one place. The temperature, flow, antifreeze and balance checks appear after a "
                 "calculation."))
    for i, check in enumerate(found):
        with st.container(border=True):
            text_col, button_col = st.columns([4, 1.6], vertical_alignment="center")
            text_col.markdown(f"{check_icons[check.level]} **{check.title}**  \n{check.detail}")
            if check.section and check.level != checks.FINE:
                step = section_step_key(check.section)
                button_col.button(t("Go to {step}", step=STEPS[step]), key=f"check.goto.{i}", width="stretch",
                                  on_click=lambda step=step: st.session_state.update(goto_step=step))


found_checks = design_checks()

def first_error_step() -> None:
    st.session_state.goto_step = section_step_key(next(iter(errors)))


with calc_slot:
    n = checks.counts(found_checks)
    with st.container(width="stretch"):
        if errors:
            ui.calc_status("bad", t("{n} input(s) need attention", n=sum(len(m) for m in errors.values())),
                           "; ".join(f"{section_step.get(k, '')}: {t(properties.get(k).label)}" for k in errors))
        elif "calc_error" in st.session_state:
            ui.calc_status("bad", t("The calculation failed"), t("Details in 📊 Results."))
        elif "result_json" in st.session_state:
            res = cached_size(st.session_state.result_json)
            last = t("{n} × {length:.1f} m, {total:,.0f} m in total", n=res.number_of_boreholes,
                     length=res.borehole_length, total=res.total_length)
            if st.session_state.result_json != current_json:
                ui.calc_status("warn", t("Inputs changed – results out of date"), t("Last result: {x}", x=last))
            else:
                ui.calc_status("ok", t("Result up to date"), last)
        else:
            ui.calc_status("grey", t("Not calculated yet"))
    if errors:
        st.button(t("Show"), on_click=first_error_step, key="calc_goto_error", icon=":material/arrow_upward:")
    check_label = " · ".join(x for x in (
        t("{n} problem(s)", n=n[checks.PROBLEM]) if n[checks.PROBLEM] else "",
        t("{n} warning(s)", n=n[checks.WARNING]) if n[checks.WARNING] else "") if x) or t("Design check")
    st.button(check_label, on_click=open_design_check, key="open_checks", help=t("Open the design check"),
              icon=":material/error:" if n[checks.PROBLEM] else ":material/warning:" if n[checks.WARNING]
              else ":material/fact_check:")
    if st.button(action, type="primary", disabled=bool(errors), icon=":material/play_arrow:", key="calc_go"):
        calculate()


# ---------------------------------------------------------------- design check (a step of its own)

with step_tabs[CHECK]:
    st.markdown("##### " + t("Design check"), help=t(
        "Every input check in one place; after a calculation also the temperature, flow, antifreeze and balance "
        "checks. Confirm to calculate and open the results."))
    show_design_check(found_checks)
    if errors:
        st.error(t("Correct the inputs marked in red first."), icon=":material/error:")
    with st.container(horizontal=True, horizontal_alignment="right", key="check_confirm_row"):
        st.button(t("Confirm and calculate"), type="primary", icon=":material/check:", disabled=bool(errors),
                  key="check_confirm", on_click=lambda: st.session_state.update(calc_requested=True))


# ---------------------------------------------------------------- results sheet (views: ghe_web/results)

ctx = None
if "result_json" in st.session_state:
    sized_json = st.session_state.result_json
    sized_inputs = model.from_json(sized_json)[1]
    result = cached_size(sized_json)
    ctx = results.Ctx(result=result, key=analysis.key_results(result, sized_inputs), sized_inputs=sized_inputs,
                      sized_json=sized_json, current_json=current_json, inputs=inputs, name=name, simple=SIMPLE,
                      found_checks=found_checks, show_design_check=show_design_check, project_json=project_json)

with step_tabs[RESULTS]:
    if "calc_error" in st.session_state:
        st.error(t("The calculation failed: {error}", error=st.session_state.calc_error), icon=":material/error:")
    if ctx is None:
        st.info(t("No result yet. Check the inputs in the steps above, then press **{action}**.", action=action),
                icon=":material/info:")
        if st.button(action, type="primary", disabled=bool(errors), key="results_calc"):
            calculate()
    else:
        if ctx.sized_json != current_json:
            st.warning(t("The inputs changed since this result was calculated. Press **{action}** to update it.",
                         action=action), icon=":material/update:")
        sections = results_registry.sheet_views(ctx)
        with st.container(horizontal=True, horizontal_alignment="right", key="sheetbar"):
            results_sheet.customize(sections)
        results_summary.answer_section(ctx)
        number = 0
        for view in sections:  # every section switched on, one below the other
            if not results_sheet.section_on(view.key):
                continue
            number += 1
            st.markdown(f"<h3 class='sheethead'>{number} · {html.escape(t(view.title))}</h3>", unsafe_allow_html=True)
            results_registry.render(view, ctx, number)
        st.markdown(f"<h3 class='sheethead'>{html.escape(t('Downloads'))}</h3>", unsafe_allow_html=True)
        results_registry.render(results_registry.get("export"), ctx, number + 1)

with step_tabs[ANALYSIS]:
    if ctx is None:
        st.info(t("The further analysis starts from a result. Calculate first."), icon=":material/info:")
    else:
        st.caption(t("Sensitivity, variants and a layout search, starting from the result in 📊 Results."))
        results_registry.render(results_registry.get("analysis"), ctx, 1)
