"""Learn mode on the page (Streamlit). It is a page of its own: pick one of the example projects
(``projects.py``) and study it in five tabs: its parameters, each with a "?" that explains it and gives its
sensitivity on this project; the sized result, explained; parameter studies and scenarios; the glossary; and the
literature.

Outside Learn mode only two things show: "Literature and sources" in the menu ☰ and a "Read more" line in the "?"
help of the fields that have a glossary entry.
"""
from __future__ import annotations

import html

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from .. import i18n
from ..charts import result_charts
from ..core import analysis, model
from ..i18n import fmt, t
from ..page import look as ui
from . import explain, glossary, projects, sources
from .text import L

ACCENT, COLD, WARM, GREY, INK = "#0e7490", "#2563eb", "#c2410c", "#94a3b8", "#13294b"
MODE = "learn"
TABS = {"params": ":material/tune: Parameters", "result": ":material/insights: Result explained",
        "explore": ":material/science: Explore", "glossary": ":material/dictionary: Glossary",
        "literature": ":material/menu_book: Literature"}
STUDIES = {"parameter": "Parameter study", "projects": "Compare the projects", "regeneration": "Regeneration",
           "ground": "Ground over time", "borehole": "Borehole resistance"}

CSS = """<style>
.learnhead {font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
  color: #0e7490; margin: .1rem 0 .35rem; display: flex; align-items: center; gap: .35rem;}
.lproj {border: 1px solid rgba(14,116,144,.25); border-radius: .8rem; padding: .9rem 1.1rem;
  background: linear-gradient(135deg, rgba(14,116,144,.06), rgba(37,99,235,.03));}
.lproj h4 {margin: 0 0 .15rem; font-size: 1.15rem;}
.lproj .lead {font-size: .85rem; opacity: .75; margin-bottom: .5rem;}
.lkeys {display: grid; grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr)); gap: .5rem; margin-top: .6rem;}
.lkeys div {background: rgba(255,255,255,.55); border: 1px solid rgba(128,128,128,.18); border-radius: .55rem;
  padding: .4rem .6rem;}
.lkeys span {display: block; font-size: .74rem; opacity: .7;}
.lkeys b {font-size: 1.05rem; font-variant-numeric: tabular-nums;}
.pgroup {font-size: .74rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; opacity: .65;
  margin: .9rem 0 .1rem; border-bottom: 1px solid rgba(128,128,128,.2); padding-bottom: .2rem;}
.pname {font-weight: 600;} .psym {font-family: ui-monospace, monospace; font-size: .8rem; opacity: .7;}
.pval {font-variant-numeric: tabular-nums; text-align: right;}
.sens {display: grid; grid-template-columns: 1fr 1fr; align-items: center; height: .7rem; position: relative;}
.sens i {display: block; height: .7rem; border-radius: 3px;}
.sens .neg {justify-self: end; background: #2563eb;} .sens .pos {justify-self: start; background: #c2410c;}
.sens::after {content: ""; position: absolute; left: 50%; top: -.15rem; bottom: -.15rem; width: 1px;
  background: rgba(128,128,128,.6);}
.sensval {font-size: .78rem; font-variant-numeric: tabular-nums; opacity: .8;}
.why {display: flex; gap: .7rem; margin: .5rem 0; align-items: flex-start; line-height: 1.5;}
.why .n {flex: none; width: 1.5rem; height: 1.5rem; border-radius: 50%; border: 1.5px solid #0e7490; color: #0e7490;
  font-weight: 700; font-size: .78rem; display: flex; align-items: center; justify-content: center;}
.why sup, .srcline sup {color: #0e7490; font-weight: 700; font-size: .68rem;}
.srcline {font-size: .8rem; opacity: .85; border-top: 1px solid rgba(128,128,128,.25); padding-top: .4rem;
  margin-top: .5rem;}
.srcline a {color: #0e7490; font-weight: 600; text-decoration: none;}
.rbparts {display: grid; gap: .35rem; margin: .2rem 0 .4rem;}
.rbrow {display: grid; grid-template-columns: 7.5rem 1fr 11rem; gap: .6rem; align-items: center; font-size: .9rem;}
.rbrow div {background: rgba(128,128,128,.15); border-radius: 4px; height: 1.1rem;}
.rbrow i {display: block; height: 100%; background: #0e7490; border-radius: 4px;}
.rbrow b {font-weight: 600; font-variant-numeric: tabular-nums;}
</style>"""


def active(mode: str | None) -> bool:
    return mode == MODE


def inject_css() -> None:
    st.html(CSS)


def _md(text: str) -> str:
    """Markdown bold (**x**) to HTML, the rest escaped."""
    parts = html.escape(text).split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def _head(icon: str, text: str) -> None:
    st.html(f"<div class='learnhead'>{ui.icon(icon)} {html.escape(text)}</div>")


def source_line(numbers, lead: str = "") -> None:
    """One small line of numbered sources, each linked to the document."""
    links = " · ".join(f"<a href='{html.escape(sources.get(n).url)}' target='_blank' rel='noopener'>[{n}]</a> "
                       f"{html.escape(sources.get(n).short)}" for n in numbers)
    st.html(f"<div class='srcline'>{ui.icon('menu_book')} {html.escape(lead) + ' ' if lead else ''}{links}</div>")


def read_more(prop_key: str) -> str | None:
    """The last line of a field's "?" help (all modes): the glossary term's sources, or None."""
    term = glossary.for_field(prop_key)
    if term is None or not term.sources:
        return None
    refs = ", ".join(f"[{sources.get(n).short}]({sources.get(n).url})" for n in term.sources)
    return t(":material/menu_book: Read more: {refs} · Learn mode explains {term}", refs=refs, term=term.name)


# ---------------------------------------------------------------- cached calculations (shared by all viewers)

@st.cache_resource(max_entries=6, show_spinner=False)
def _sized(project_key: str):
    project = projects.BY_KEY[project_key]
    inputs = project.inputs()
    result = model.size(inputs)
    return inputs, result, analysis.key_results(result, inputs)


@st.cache_data(max_entries=6, show_spinner=False)
def _sensitivities(project_key: str) -> dict:
    stored = projects.stored().get(project_key)
    if stored:
        return stored["sensitivity"]
    return projects.compute(projects.BY_KEY[project_key])["sensitivity"]


@st.cache_data(max_entries=40, show_spinner=False)
def _study(project_key: str, param: str) -> pd.DataFrame:
    p = projects.BY_PARAM[tuple(param.split("."))]
    inputs = _sized(project_key)[0]
    return projects.study(inputs, p, projects.study_values(inputs, p, n=7))


@st.cache_data(max_entries=6, show_spinner=False)
def _regeneration(project_key: str) -> pd.DataFrame:
    return projects.regeneration_study(_sized(project_key)[0])


@st.cache_resource(max_entries=12, show_spinner=False)
def _ground(project_key: str, years: int):
    return analysis.ground_temperature_map(_sized(project_key)[1], cells=60, years=years)


@st.cache_data(max_entries=6, show_spinner=False)
def _borehole(project_key: str) -> dict:
    import copy
    inputs, result, _ = _sized(project_key)
    out = {"grout": [], "flow": []}
    for kg in (0.8, 1.6, 2.4):
        trial = copy.deepcopy(inputs)
        trial["pipe"].values["k_g"] = kg
        r = model.size(trial)
        out["grout"].append({"Value": kg, "Rb": r.borehole_resistance, "Length": r.borehole_length})
    base = float(inputs["flow"].values["mfr"])
    for factor in (0.4, 0.7, 1.0, 1.5):
        trial = copy.deepcopy(inputs)
        trial["flow"].values["mfr"] = round(base * factor, 3)
        r = model.size(trial)
        out["flow"].append({"Value": round(base * factor, 3), "Rb": r.borehole_resistance, "Length": r.borehole_length,
                            "Re": r.reynolds})
    return out


# ---------------------------------------------------------------- the Learn page

def page(state) -> None:
    """Learn mode: the project picker, the project card and the five tabs."""
    inject_css()
    st.markdown("### " + t("Learn with example projects"))
    st.caption(L("Three sized reference cases. Every number on this page comes from the same GHEtool sizing as a "
                 "real project; change the case to see how the governing mechanisms shift.",
                 "Drei ausgelegte Referenzfälle. Jede Zahl auf dieser Seite stammt aus derselben GHEtool-Auslegung "
                 "wie bei einem echten Projekt; wechseln Sie den Fall, um zu sehen, wie sich die maßgebenden "
                 "Mechanismen verschieben."))
    key = st.segmented_control(t("Example project"), [p.key for p in projects.PROJECTS], default="house",
                               required=True, key="learn_project", label_visibility="collapsed",
                               format_func=_in_language(lambda k: projects.BY_KEY[k].title))
    project = projects.BY_KEY[key]
    with st.spinner(t("Sizing the example project...")):
        inputs, result, key_results = _sized(key)
    _project_card(project, result, key_results)
    names = [t(v) for v in TABS.values()]
    tab = dict(zip(TABS, st.tabs(names, key="learn_tab", on_change="rerun")))
    with tab["params"]:
        _parameters(project, inputs)
    with tab["result"]:
        _result(project, inputs, result, key_results)
    with tab["explore"]:
        _explore(project, inputs, result)
    with tab["glossary"]:
        glossary_tab()
    with tab["literature"]:
        literature_tab()


def _project_card(project: projects.Project, result, key_results) -> None:
    v = key_results.values
    b = analysis.coldest_breakdown(result)
    items = [(t("Boreholes"), fmt("{n} × {h:,.1f} m", n=result.number_of_boreholes, h=result.borehole_length)),
             (t("Total length"), fmt("{x:,.0f} m", x=result.total_length)),
             ("R_b*", fmt("{x:.3f} m·K/W", x=result.borehole_resistance)),
             ("Re", fmt("{x:,.0f}", x=result.reynolds or 0)),
             (t("Net extraction"), fmt("{x:,.1f} MWh/a", x=float(v.get("extraction_mwh", 0)) -
                                       float(v.get("injection_mwh", 0)))),
             (t("Limiting"), fmt("{f:.1f} °C · {when}", f=b["fluid"], when=t("year {n}", n=b["year"]))
              if b else "–")]
    keys = "".join(f"<div><span>{html.escape(a)}</span><b>{html.escape(c)}</b></div>" for a, c in items)
    st.html(f"<div class='lproj'><h4>{html.escape(project.title)}</h4><div class='lead'>{html.escape(project.lead)}"
            f"</div>{_md(project.text)}<div class='lkeys'>{keys}</div></div>")


def _in_language(func):
    """A widget's format_func in the language of this run: Streamlit may call it outside the run (test runner)."""
    language = i18n.language()

    def call(value):
        with i18n.using(language):
            return func(value)
    return call


# ---------------------------------------------------------------- tab: parameters

def _fmt_value(x: float, unit: str, step: float | None = None) -> str:
    digits = 0 if abs(x) >= 100 or (step is not None and float(step).is_integer() and float(x).is_integer()) \
        else 1 if abs(x) >= 10 else 2
    return (fmt("{x:,.%df}" % digits, x=x) + " " + unit).strip()


def _sens_text(p: projects.Parameter, s: float | None) -> str:
    if s is None:
        return "–"
    if p.kind == "abs":
        return fmt("{x:+.1f} m/K", x=s)
    return fmt("ε = {x:+.2f}", x=s)


def _sens_bar(p: projects.Parameter, s: float | None, length: float) -> str:
    if s is None:
        return "<div class='sens'></div>"
    rel = s if p.kind == "rel" else s / length  # per K -> relative per K
    width = min(abs(rel), 1.0) * 100
    side = "neg" if rel < 0 else "pos"
    bar = f"<i class='{side}' style='width:{width:.0f}%'></i>"
    return f"<div class='sens'>{bar if side == 'neg' else '<span></span>'}{bar if side == 'pos' else ''}</div>"


def _parameters(project: projects.Project, inputs) -> None:
    sens = _sensitivities(project.key)
    length = _sized(project.key)[1].borehole_length
    st.caption(L("Local sensitivity of the required length on this project, by central differences of the sizing: "
                 "the elasticity ε = (ΔL/L)/(Δx/x) for ±10 %, or ΔL/ΔT in m/K for temperatures. Blue shortens, "
                 "red lengthens. The ? opens the definition, the governing relation and the sources.",
                 "Lokale Sensitivität der erforderlichen Länge in diesem Projekt, aus zentralen Differenzen der "
                 "Auslegung: die Elastizität ε = (ΔL/L)/(Δx/x) für ±10 %, bzw. ΔL/ΔT in m/K für Temperaturen. Blau "
                 "verkürzt, Rot verlängert. Das ? öffnet Definition, maßgebende Beziehung und Quellen."))
    group = None
    for p in projects.PARAMETERS:
        if p.group != group:
            group = p.group
            st.html(f"<div class='pgroup'>{html.escape(L(*projects.GROUPS[group]))}</div>")
        q = projects.prop(p)
        term = glossary.BY_KEY[p.term]
        s = sens.get(f"{p.section}.{p.key}")
        name, value, bar, number, more = st.columns([3.0, 1.4, 2.0, 1.1, 0.4], vertical_alignment="center", gap="small")
        symbol = _symbol(p)
        name.html(f"<span class='pname'>{html.escape(p.name)}</span> "
                  f"<span class='psym'>{html.escape(symbol)}</span>")
        value.html(f"<div class='pval'>{html.escape(_fmt_value(projects.value(inputs, p), t(q.unit or ''), q.step))}</div>")
        bar.html(_sens_bar(p, s, length))
        number.html(f"<span class='sensval'>{html.escape(_sens_text(p, s))}</span>")
        with more.popover("", icon=":material/help:", help=t("Explanation, equation and sources")):
            _term_body(term, p, s, project)


def _term_body(term: glossary.Term, p: projects.Parameter | None = None, s: float | None = None,
               project: projects.Project | None = None) -> None:
    st.markdown(f"**{term.name}**" + (f"  ·  `{term.symbol}`" if term.symbol else ""))
    st.markdown(term.text)
    if term.equation:
        st.latex(term.equation)
    if term.practice:
        st.markdown(f"*{L('In practice', 'In der Praxis')}:* {term.practice}")
    if p is not None and s is not None and project is not None:
        if p.kind == "abs":
            st.markdown(fmt(L("**On this project:** +1 K changes the length by {x:+.1f} m per borehole.",
                              "**In diesem Projekt:** +1 K ändert die Länge um {x:+.1f} m je Sonde."), x=s))
        else:
            st.markdown(fmt(L("**On this project:** ε = {e:+.2f}, so +10 % changes the length by about {x:+.1f} %.",
                              "**In diesem Projekt:** ε = {e:+.2f}, +10 % ändern die Länge also um etwa {x:+.1f} %."),
                            e=s, x=10 * s))
    if term.sources:
        source_line(term.sources)
    if p is not None:
        st.button(t("Study this parameter"), icon=":material/show_chart:", key=f"learn_go.{p.section}.{p.key}",
                  on_click=_go_study, args=(f"{p.section}.{p.key}",))


def _go_study(param: str) -> None:
    st.session_state["learn_study"] = "parameter"
    st.session_state["learn_param"] = param
    st.session_state["learn_tab"] = t(TABS["explore"])


# ---------------------------------------------------------------- tab: result explained

def _waterfall_chart(b: dict) -> alt.Chart:
    rows = pd.DataFrame(b["rows"])
    rows["Low"] = rows[["Start", "End"]].min(axis=1)
    rows["High"] = rows[["Start", "End"]].max(axis=1)
    rows["Label"] = [fmt("{x:.1f} °C", x=r.End) if r.Kind in ("ground", "fluid") else fmt("{x:+.2f} K", x=r.Change)
                     for r in rows.itertuples()]
    colours = {"ground": GREY, "Long term": "#1e40af", "Month": "#3b82f6", "Peak (ground)": "#60a5fa",
               "Borehole": ACCENT, "fluid": INK}
    order = list(rows["Part"])
    x = alt.X("Part:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelLimit=120,
                                                                labelExpr="split(datum.label, ' ')"))
    bars = alt.Chart(rows).mark_bar(cornerRadius=3, size=44).encode(
        x=x, y=alt.Y("Low:Q", title=t("Temperature [°C]")), y2="High:Q",
        color=alt.Color("Kind:N", scale=alt.Scale(domain=list(colours), range=list(colours.values())), legend=None),
        tooltip=[alt.Tooltip("Part:N", title=t("Part")), alt.Tooltip("Label:N", title=t("Value"))])
    text = alt.Chart(rows).mark_text(dy=-8, fontWeight="bold").encode(x=x, y="High:Q", text="Label:N")
    limit = alt.Chart(pd.DataFrame({"y": [b["limit"]]})).mark_rule(strokeDash=[6, 4], color=COLD).encode(y="y:Q")
    return (bars + text + limit).properties(height=280)


def _yearly_chart(result) -> alt.Chart:
    df = analysis.yearly_extremes(result)
    long = df.melt("Year", ["Lowest", "Highest"], var_name="Kind", value_name="T")
    long["Kind"] = long["Kind"].map({"Lowest": t("Yearly minimum"), "Highest": t("Yearly maximum")})
    lims = result.borefield
    rules = pd.DataFrame({"y": [lims.Tf_min, lims.Tf_max]})
    lines = alt.Chart(long).mark_line(strokeWidth=2.5).encode(
        x=alt.X("Year:Q", title=t("Year")), y=alt.Y("T:Q", title=t("Mean fluid temperature [°C]")),
        color=alt.Color("Kind:N", title=None, scale=alt.Scale(range=[COLD, WARM]), legend=alt.Legend(orient="top")))
    rule = alt.Chart(rules).mark_rule(strokeDash=[6, 4], color=GREY).encode(y="y:Q")
    return (lines + rule).properties(height=240)


def _result(project, inputs, result, key_results) -> None:
    steps = explain.why(result, key_results)
    b = explain.breakdown(result)
    left, right = st.columns([1, 1.15], gap="medium")
    with left, st.container(border=True):
        _head("insights", t("Why {h:,.1f} m per borehole?", h=result.borehole_length))
        numbered = []
        for i, step in enumerate(steps, 1):
            refs = "<sup>" + ",".join(str(n) for n in step.sources) + "</sup>" if step.sources else ""
            numbered.append(f"<div class='why'><div class='n'>{i}</div><div><b>{html.escape(step.title)}.</b> "
                            f"{_md(step.text)}{refs}</div></div>")
        st.html("".join(numbered))
        source_line(sorted({n for s in steps for n in s.sources}))
    with right, st.container(border=True):
        if b is None:
            _head("waterfall_chart", t("Temperature budget"))
            st.caption(t("The breakdown needs monthly results."))
        else:
            _head("waterfall_chart", t("Temperature budget of the limiting month"))
            ui.show_chart(_waterfall_chart(b))
            st.caption(fmt(L("Superposition at the limiting month: T_g minus the long-term, monthly and peak responses "
                             "of the ground and the borehole term q_h·R_b = {q:.1f} W/m × {rb:.3f} m·K/W. The parts "
                             "add up exactly to the limiting mean fluid temperature.",
                             "Überlagerung im maßgebenden Monat: T_g minus Langzeit-, Monats- und Spitzenantwort des "
                             "Untergrunds und der Bohrlochterm q_h·R_b = {q:.1f} W/m × {rb:.3f} m·K/W. Die Anteile "
                             "ergeben exakt die maßgebende mittlere Fluidtemperatur."), q=b["q_peak"], rb=b["Rb"]))
            source_line((1, 3))
    with st.container(border=True):
        _head("show_chart", t("Yearly extremes of the mean fluid temperature"))
        ui.show_chart(_yearly_chart(result))
        st.caption(L("Dashed: the limits. A minimum that still falls in the last years indicates a net imbalance whose "
                     "long-term response has not settled; the slope reflects the late-time g-function.",
                     "Gestrichelt: die Grenzen. Ein Minimum, das in den letzten Jahren noch fällt, zeigt eine "
                     "Nettobilanz, deren Langzeitantwort nicht abgeklungen ist; die Steigung spiegelt die g-Funktion "
                     "bei großen Zeiten."))
    with st.expander(t("Method: how GHEtool sizes"), icon=":material/functions:"):
        st.markdown(L(
            "The mean fluid temperature is obtained by temporal superposition of three load pulses on the field's "
            "g-function (Eskilson 1987; Peere et al. 2021). For the yearly average load q_y, the monthly load q_m "
            "and the monthly peak q_h (duration t_p), each per metre of borehole:",
            "Die mittlere Fluidtemperatur ergibt sich durch zeitliche Überlagerung dreier Lastpulse auf der "
            "g-Funktion des Feldes (Eskilson 1987; Peere et al. 2021). Für die mittlere Jahreslast q_y, die "
            "Monatslast q_m und die Monatsspitze q_h (Dauer t_p), jeweils je Meter Sonde:"))
        st.latex(r"T_f = T_g - q_y R_y - q_m R_m - q_h R_h - q_h R_b^*")
        st.latex(r"R_y = \frac{g(t_{\mathrm{end}}) - g(t_{\mathrm{end}}-t_m)}{2\pi\lambda},\quad "
                 r"R_m = \frac{g(t_m) - g(t_p)}{2\pi\lambda},\quad R_h = \frac{g(t_p)}{2\pi\lambda}")
        st.markdown(L(
            "Because the ground resistances depend on H through the g-function, the condition "
            "T_f(H) = T_f,limit is solved iteratively. L2 evaluates it for the first and the last year, L3 for every "
            "month, L4 hour by hour. The projects here are sized with L3 (building loads with monthly resolution).",
            "Da die Untergrundwiderstände über die g-Funktion von H abhängen, wird die Bedingung "
            "T_f(H) = T_f,Grenze iterativ gelöst. L2 wertet sie für das erste und das letzte Jahr aus, L3 für jeden "
            "Monat, L4 stündlich. Die Projekte hier sind mit L3 ausgelegt (Gebäudelasten in monatlicher Auflösung)."))
        source_line((1, 3, 2, 7))


# ---------------------------------------------------------------- tab: explore

def _line(df: pd.DataFrame, x: str, x_title: str, now: float | None = None, y_title: str | None = None,
          color: str | None = None) -> alt.Chart:
    data = df.dropna()
    enc = dict(x=alt.X(f"{x}:Q", title=x_title, axis=alt.Axis(tickCount=8)),
               y=alt.Y("Length:Q", title=y_title or t("Required length per borehole [m]"), scale=alt.Scale(zero=False)))
    if color:
        enc["color"] = alt.Color(f"{color}:N", title=None, legend=alt.Legend(orient="top", labelLimit=300),
                                 scale=alt.Scale(range=[ACCENT, WARM, COLD]))
        base = alt.Chart(data).encode(**enc)
        layers = [base.mark_line(strokeWidth=2.5), base.mark_circle(size=40)]
    else:
        base = alt.Chart(data).encode(**enc)
        layers = [base.mark_line(color=ACCENT, strokeWidth=3), base.mark_circle(color=ACCENT, size=45)]
    if now is not None:
        layers.append(alt.Chart(pd.DataFrame({"x": [now]})).mark_rule(strokeDash=[5, 4], color=GREY).encode(x="x:Q"))
    return alt.layer(*layers).properties(height=300)


def _explore(project, inputs, result) -> None:
    pick = st.segmented_control(t("Study"), list(STUDIES), format_func=_in_language(lambda k: t(STUDIES[k])), default="parameter",
                                required=True, key="learn_study", label_visibility="collapsed")
    if pick == "parameter":
        _study_parameter(project, inputs)
    elif pick == "projects":
        _study_projects()
    elif pick == "regeneration":
        _study_regeneration(project, inputs)
    elif pick == "ground":
        _study_ground(project, result)
    else:
        _study_borehole(project, result)


def _symbol(p: projects.Parameter) -> str:
    return p.symbol or glossary.BY_KEY[p.term].symbol.split(" [")[0]


def _param_label(param: str) -> str:
    p = projects.BY_PARAM[tuple(param.split("."))]
    q = projects.prop(p)
    return f"{p.name} [{t(q.unit)}]" if q.unit else p.name


def _study_parameter(project, inputs) -> None:
    options = [f"{p.section}.{p.key}" for p in projects.PARAMETERS]
    param = st.selectbox(t("Parameter"), options, format_func=_in_language(_param_label), key="learn_param")
    p = projects.BY_PARAM[tuple(param.split("."))]
    term = glossary.BY_KEY[p.term]
    with st.spinner(t("Sizing the project for every value...")):
        df = _study(project.key, param)
    now = projects.value(inputs, p)
    ui.show_chart(_line(df, "Value", _param_label(param), now))
    s = _sensitivities(project.key).get(param)
    valid = df.dropna()
    if len(valid) >= 2:
        span = float(valid["Length"].max() - valid["Length"].min())
        st.caption(fmt(L("Seven sizings with all other inputs fixed (dashed: this project). Range of the required "
                         "length: {a:,.1f}–{b:,.1f} m, a span of {p:.0f} % of this project's length. Local sensitivity: {s}.",
                         "Sieben Auslegungen bei sonst festen Eingaben (gestrichelt: dieses Projekt). Spanne der "
                         "erforderlichen Länge: {a:,.1f}–{b:,.1f} m, eine Spanne von {p:.0f} % der Länge dieses Projekts. Lokale "
                         "Sensitivität: {s}."),
                       a=float(valid["Length"].min()), b=float(valid["Length"].max()),
                       p=span / _sized(project.key)[1].borehole_length * 100, s=_sens_text(p, s)))
    with st.expander(fmt(L("About {x}", "Zu {x}"), x=term.name), icon=":material/help:"):
        _term_body(term)


def _study_projects() -> None:
    st.caption(L("The same relative change applied to all three projects. Normalised: L/L₀ over x/x₀. The slopes at "
                 "1 are the elasticities; differences show which mechanism governs each case.",
                 "Dieselbe relative Änderung in allen drei Projekten. Normiert: L/L₀ über x/x₀. Die Steigungen bei 1 "
                 "sind die Elastizitäten; Unterschiede zeigen, welcher Mechanismus den jeweiligen Fall bestimmt."))
    options = [f"{p.section}.{p.key}" for p in projects.PARAMETERS if p.kind == "rel" and p.key != "peak_cooling_kw"]
    param = st.selectbox(t("Parameter"), options, format_func=_in_language(_param_label), key="learn_param_cmp",
                         index=options.index("borefield.B_1"))
    p = projects.BY_PARAM[tuple(param.split("."))]
    frames = []
    with st.spinner(t("Sizing the three projects for every value...")):
        for project in projects.PROJECTS:
            inputs, result, _ = _sized(project.key)
            df = _study(project.key, param).copy()
            now = projects.value(inputs, p)
            base = result.borehole_length
            df["Value"] = df["Value"] / now
            df["Length"] = df["Length"] / base
            df["Project"] = project.title
            frames.append(df)
    ui.show_chart(_line(pd.concat(frames), "Value", fmt("{x} / {x}₀", x=_symbol(p)), 1.0,
                        t("Required length L / L₀"), color="Project"))
    rows = [{t("Project"): pr.title, "ε": _sensitivities(pr.key).get(param)} for pr in projects.PROJECTS]
    st.dataframe(pd.DataFrame(rows), hide_index=True,
                 column_config={"ε": st.column_config.NumberColumn("ε = (ΔL/L)/(Δx/x)", format="%+.2f")})


def _study_regeneration(project, inputs) -> None:
    st.caption(L("Heat returned to the ground as a share of the annual extraction (passive cooling with the project's "
                 "SEER, 1,000 full-load hours). The other inputs stay fixed.",
                 "Rückgeführte Wärme als Anteil des jährlichen Entzugs (passive Kühlung mit der SEER des Projekts, "
                 "1.000 Volllaststunden). Die übrigen Eingaben bleiben fest."))
    with st.spinner(t("Sizing the project for every share...")):
        df = _regeneration(project.key).copy()
    df["Percent"] = df["Share"] * 100
    ui.show_chart(_line(df, "Percent", t("Regeneration Q_inj / Q_ext [%]")))
    valid = df.dropna()
    if len(valid) >= 2:
        best = valid.loc[valid["Length"].idxmin()]
        st.markdown(fmt(L("Shortest length at **{s:.0f} %** regeneration ({l:,.1f} m, {d:+.0f} % vs. none). Beyond the "
                          "optimum the summer maximum becomes limiting and the length rises again.",
                          "Kürzeste Länge bei **{s:.0f} %** Regeneration ({l:,.1f} m, {d:+.0f} % gegenüber keiner). "
                          "Jenseits des Optimums wird das Sommermaximum maßgebend und die Länge steigt wieder."),
                        s=best["Percent"], l=best["Length"],
                        d=(best["Length"] / valid["Length"].iloc[0] - 1) * 100))
    source_line((1, 9))


def _study_ground(project, result) -> None:
    years = st.segmented_control(t("Year"), [1, 5, 25, 50], default=50, required=True, key="learn_year",
                                 format_func=_in_language(lambda n: t("year {n}", n=n)))
    with st.spinner(t("Calculating the ground temperature around the field...")):
        end = _ground(project.key, 50)
        m = _ground(project.key, years)
    if not m or not end:
        st.info(t("No ground map for this project."))
        return
    scale = (float(end["table"]["Change"].min()), float(end["table"]["Change"].max()))
    left, right = st.columns([11, 9], gap="medium")
    with left:
        ui.show_chart(result_charts.ground_map_chart({**m, "scale": scale}, size=300 if ui.is_phone() else 420),
                      width="content")
    with right:
        st.metric(t("Largest change"), fmt("{x:.1f} K", x=float(m["table"]["Change"].min())))
        st.caption(L("Temperature change at mid-depth caused by the net annual imbalance (finite line source with "
                     "mirror image, superposed over all boreholes; seasonal swings average out and are left out). "
                     "Colours are fixed to year 50, so the years compare. Inner boreholes cool most: their "
                     "neighbours' fields overlap, which is what the late-time g-function describes.",
                     "Temperaturänderung in halber Tiefe durch die Netto-Jahresbilanz (finite Linienquelle mit "
                     "Spiegelquelle, über alle Sonden überlagert; saisonale Schwankungen mitteln sich aus und fehlen). "
                     "Die Farben sind auf Jahr 50 festgelegt, damit die Jahre vergleichbar sind. Innere Sonden kühlen "
                     "am stärksten ab: die Felder der Nachbarn überlagern sich, genau das beschreibt die g-Funktion bei "
                     "großen Zeiten."))
        source_line((3, 7))


def _study_borehole(project, result) -> None:
    parts = explain.resistance_parts(result, result.borefield.Tf_min)
    b = analysis.coldest_breakdown(result)
    q = b["q_peak"] if b else 0.0
    if parts:
        rows = "".join(
            f"<div class='rbrow'><span>{html.escape(name)}</span><div><i style='width:{r / max(x for _, x in parts) * 100:.1f}%'>"
            f"</i></div><b>{html.escape(fmt('{r:.3f} m·K/W · {k:.2f} K', r=r, k=r * q))}</b></div>"
            for name, r in parts)
        st.html(f"<div class='rbparts'>{rows}</div>")
        st.caption(fmt(L("R_b* = {rb:.3f} m·K/W at the lowest fluid temperature, split approximately (film and pipe "
                         "wall of the legs in parallel, grout as the remainder of the multipole result). At the peak "
                         "of {q:.1f} W/m the fluid runs {k:.2f} K below the borehole wall.",
                         "R_b* = {rb:.3f} m·K/W bei der tiefsten Fluidtemperatur, näherungsweise aufgeteilt (Film und "
                         "Rohrwand der Schenkel parallel, Verfüllung als Rest des Multipol-Ergebnisses). Bei der "
                         "Spitze von {q:.1f} W/m liegt das Fluid {k:.2f} K unter der Bohrlochwand."),
                       rb=result.borehole_resistance, q=q, k=result.borehole_resistance * q))
    with st.spinner(t("Sizing the project with other grouts and flow rates...")):
        data = _borehole(project.key)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**" + t("Grout thermal conductivity") + "**")
        g = pd.DataFrame(data["grout"]).rename(columns={"Value": "λ_g [W/(m·K)]", "Rb": "R_b* [m·K/W]",
                                                       "Length": t("Length [m]")})
        st.dataframe(g.round({"R_b* [m·K/W]": 3, t("Length [m]"): 1}), hide_index=True, width="stretch")
    with c2:
        st.markdown("**" + t("Mass flow rate per borehole") + "**")
        f = pd.DataFrame(data["flow"])
        f["Re"] = f["Re"].round(0)
        f = f.rename(columns={"Value": "ṁ [kg/s]", "Rb": "R_b* [m·K/W]", "Length": t("Length [m]")})
        st.dataframe(f.round({"R_b* [m·K/W]": 3, t("Length [m]"): 1}), hide_index=True, width="stretch")
    st.caption(L("Below Re ≈ 2,300 the film resistance jumps (Nu ≈ 4.36) and R_b* with it; above it, more flow mainly "
                 "costs pumping power. The grout term scales with 1/λ_g and usually dominates.",
                 "Unter Re ≈ 2.300 springt der Filmwiderstand (Nu ≈ 4,36) und mit ihm R_b*; darüber kostet mehr "
                 "Durchfluss vor allem Pumpenleistung. Der Verfüllterm skaliert mit 1/λ_g und dominiert meist."))
    source_line((7, 4))


# ---------------------------------------------------------------- tabs: glossary, literature

def glossary_tab() -> None:
    find = st.text_input(t("Search"), placeholder=t("e.g. borehole resistance"), key="learn_find",
                         label_visibility="collapsed", icon=":material/search:").strip().lower()
    for term in sorted(glossary.TERMS, key=lambda x: x.name.lower()):
        if find and find not in (term.name + " " + term.text + " " + term.symbol).lower():
            continue
        with st.expander(f"**{term.name}**" + (f"  ·  {term.symbol}" if term.symbol else "")):
            _term_body(term)


def literature_table(free_only: bool = False) -> None:
    rows = []
    for s in sources.SOURCES:
        if free_only and not s.free:
            continue
        access = t("free") if s.free else t("paid · ask the library")
        rows.append(f"| [{s.number}] | **[{s.title}]({s.url})**<br>{s.authors} · {s.venue} · {s.year} · {s.language}"
                    f" | {s.why} | {access} |")
    st.markdown(f"| | {t('Title')} | {t('Why read it')} | {t('Access')} |\n"
                "|---|---|---|---|\n" + "\n".join(rows), unsafe_allow_html=True)


def literature_tab() -> None:
    st.caption(t("One numbered list for the whole app: a number like [4] in a card or the glossary is the entry "
                 "here. {free} of {n} are free to read online. Links checked on {date}.",
                 free=sum(s.free for s in sources.SOURCES), n=len(sources.SOURCES), date=sources.CHECKED))
    with st.container(horizontal=True, vertical_alignment="bottom"):
        free = st.toggle(t("Free only"), key="learn_lit_free")
        st.download_button(t("List (text)"), sources.plain_list().encode(), "ghetool-literature.txt", "text/plain",
                           icon=":material/download:", on_click="ignore")
        st.download_button("BibTeX", sources.bibtex().encode(), "ghetool-literature.bib", "application/x-bibtex",
                           icon=":material/download:", on_click="ignore")
    literature_table(free)


def menu_button() -> None:
    """In the menu ☰, in every mode: the literature list without switching to Learn."""
    if st.button(t("Literature and sources"), icon=":material/menu_book:", width="stretch", key="menu_literature"):
        _literature_dialog()


@st.dialog(" ", width="large")
def _literature_dialog() -> None:
    st.markdown("#### " + t("Literature and sources"))
    literature_tab()
