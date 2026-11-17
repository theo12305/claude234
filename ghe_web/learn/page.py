"""Learn mode on the page (Streamlit): the explanations under the result, the three Learn tabs (introduction,
glossary, literature), the exercises, the "Read more" line of a field's help and the literature in the menu.

Nothing here shows in Simple or Expert except the literature button in the menu and the one-line "Read more" in the
"?" help of some fields.
"""
from __future__ import annotations

import html

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from .. import i18n
from ..charts import result_charts
from ..core import model
from ..page import look as ui
from ..i18n import fmt, t
from . import exercises, explain, glossary, modules, sources
from .text import L

ACCENT, COLD, WARM, GREY = "#0e7490", "#1d4ed8", "#c2410c", "#94a3b8"
MODE = "learn"

CSS = """<style>
.learnhead {font-size: .78rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
  color: var(--primary-color, #0e7490); margin: .2rem 0 .3rem;}
.rbparts {display: grid; gap: .35rem; margin: .2rem 0 .4rem;}
.rbrow {display: grid; grid-template-columns: 7.5rem 1fr 11rem; gap: .6rem; align-items: center; font-size: .9rem;}
.rbrow div {background: #e2e8f0; border-radius: 4px; height: 1.1rem;}
.rbrow i {display: block; height: 100%; background: #0e7490; border-radius: 4px;}
.rbrow b {font-weight: 600; font-variant-numeric: tabular-nums;}
.why {display: flex; gap: .7rem; margin: .45rem 0; align-items: flex-start; line-height: 1.45;}
.why .n {flex: none; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #0e7490; color: #fff;
  font-weight: 700; font-size: .85rem; display: flex; align-items: center; justify-content: center;}
.why sup, .srcline sup {color: #0e7490; font-weight: 700; font-size: .68rem;}
.srcline {font-size: .8rem; opacity: .8; border-top: 1px solid rgba(128,128,128,.25); padding-top: .4rem;
  margin-top: .4rem;}
.srcline a {color: #0e7490; font-weight: 600; text-decoration: none;}
.modmeta {font-size: .8rem; opacity: .75;}
.okbox {background: rgba(22,163,74,.12); border: 1px solid rgba(22,163,74,.45); border-radius: .6rem;
  padding: .55rem .8rem; margin: .4rem 0;}
.nobox {background: rgba(217,119,6,.12); border: 1px solid rgba(217,119,6,.45); border-radius: .6rem;
  padding: .55rem .8rem; margin: .4rem 0;}
</style>"""


def active(mode: str | None) -> bool:
    return mode == MODE


def inject_css() -> None:
    st.html(CSS)


def _md(text: str) -> str:
    """Markdown bold (**x**) to HTML, the rest escaped."""
    parts = html.escape(text).split("**")
    return "".join(f"<b>{p}</b>" if i % 2 else p for i, p in enumerate(parts))


def source_line(numbers, lead: str = "") -> None:
    """One small line of numbered sources, each linked to the document."""
    links = " · ".join(f"<a href='{html.escape(sources.get(n).url)}' target='_blank' rel='noopener'>[{n}]</a> "
                       f"{html.escape(sources.get(n).short)}" for n in numbers)
    st.html(f"<div class='srcline'>{ui.icon('menu_book')} {html.escape(lead) + ' ' if lead else ''}{links}</div>")


def term_popovers(keys) -> None:
    """The glossary entries of a few terms, each behind a small button."""
    terms = [glossary.BY_KEY[k] for k in keys if k in glossary.BY_KEY]
    if not terms:
        return
    with st.container(horizontal=True, gap="small"):
        for term in terms:
            with st.popover(term.name, icon=":material/menu_book:"):
                st.markdown(f"**{term.name}**" + (f" · `{term.symbol}`" if term.symbol else ""))
                st.markdown(term.text)
                st.caption(t("Sources: {list}", list=", ".join(f"[{n}] {sources.get(n).short}"
                                                               for n in term.sources)))
                st.caption(t("Explained in module {n}: {title}", n=term.module,
                             title=modules.BY_NUMBER[term.module].title))


def read_more(prop_key: str) -> str | None:
    """The last line of a field's "?" help: the glossary term's sources and module, or None."""
    term = glossary.for_field(prop_key)
    if term is None:
        return None
    refs = ", ".join(f"[{sources.get(n).short}]({sources.get(n).url})" for n in term.sources)
    return t(":material/menu_book: Read more: {refs} · Learn module {n}", refs=refs, n=term.module)


# ---------------------------------------------------------------- explanations under the result

@st.cache_resource(max_entries=8, show_spinner=False)
def _breakdown(project_json: str, language: str):
    from ..results.cache import cached_size
    with i18n.using(language):
        return explain.breakdown(cached_size(project_json))


def _waterfall_chart(b: dict) -> alt.Chart:
    rows = pd.DataFrame(b["rows"])
    rows["Order"] = range(len(rows))
    rows["Low"] = rows[["Start", "End"]].min(axis=1)
    rows["High"] = rows[["Start", "End"]].max(axis=1)
    rows["Label"] = [fmt("{x:.1f} °C", x=r.End) if r.Kind in ("ground", "fluid") else fmt("{x:+.1f} K", x=r.Change)
                     for r in rows.itertuples()]
    colours = {"ground": GREY, "Long term": COLD, "Month": "#3b82f6", "Peak (ground)": "#60a5fa",
               "Borehole": ACCENT, "fluid": "#13294b"}
    order = list(rows["Part"])
    x = alt.X("Part:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelLimit=110,
                                                                labelExpr="split(datum.label, ' ')"))
    bars = alt.Chart(rows).mark_bar(cornerRadius=3, size=46).encode(
        x=x, y=alt.Y("Low:Q", title=t("Temperature [°C]")), y2="High:Q",
        color=alt.Color("Kind:N", scale=alt.Scale(domain=list(colours), range=list(colours.values())), legend=None),
        tooltip=[alt.Tooltip("Part:N", title=t("Part")), alt.Tooltip("Label:N", title=t("Value"))])
    text = alt.Chart(rows).mark_text(dy=-8, fontWeight="bold").encode(x=x, y="High:Q", text="Label:N")
    limit = alt.Chart(pd.DataFrame({"y": [b["limit"]]})).mark_rule(strokeDash=[6, 4], color=COLD).encode(y="y:Q")
    return (bars + text + limit).properties(height=260)


def results_cards(ctx) -> None:
    """Under the answer card: why this length, where the degrees go, the method, terms and sources."""
    result, key = ctx.result, ctx.key
    inject_css()
    steps = explain.why(result, key)
    b = _breakdown(ctx.sized_json, i18n.language())
    left, right = st.columns([1, 1.1], gap="medium")
    with left, st.container(border=True):
        st.html(f"<div class='learnhead'>{ui.icon('school')} "
                + html.escape(t("Why {h:,.1f} m?", h=result.borehole_length)) + "</div>")
        numbered = []
        for i, step in enumerate(steps, 1):
            refs = "<sup>" + ",".join(str(n) for n in step.sources) + "</sup>" if step.sources else ""
            numbered.append(f"<div class='why'><div class='n'>{i}</div><div><b>{html.escape(step.title)}.</b> "
                            f"{_md(step.text)}{refs}</div></div>")
        st.html("".join(numbered))
        st.caption(t("Uses this project's numbers and changes with every input."))
        source_line(sorted({n for s in steps for n in s.sources}))
    with right, st.container(border=True):
        if b is None:
            st.html(f"<div class='learnhead'>{ui.icon('school')} {html.escape(t('Where the degrees go'))}</div>")
            st.caption(t("The breakdown needs monthly results. With hourly sizing, see the temperature chart."))
        else:
            head = t("Where the degrees go (coldest month)") if b["cold"] else t("Where the degrees go (warmest month)")
            st.html(f"<div class='learnhead'>{ui.icon('school')} {html.escape(head)}</div>")
            ui.show_chart(_waterfall_chart(b))
            st.caption(t("The undisturbed ground plus four parts gives the limiting fluid temperature. The last part "
                         "is the peak heat flow ({q:.1f} W/m) times the borehole resistance R_b ({rb:.3f} m·K/W).",
                         q=b["q_peak"], rb=b["Rb"]))
            source_line((1, 3))
    with st.expander(t("The method behind it"), icon=":material/functions:"):
        st.markdown(L(
            "GHEtool checks the mean fluid temperature in every month. It adds the ground's response to the yearly "
            "average load, to the month's load and to the month's peak, each as heat flow per metre times a "
            "thermal resistance of the ground taken from the field's g-function, plus the drop inside the "
            "borehole:",
            "GHEtool prüft die mittlere Fluidtemperatur in jedem Monat. Es addiert die Antwort des Untergrunds auf "
            "die mittlere Jahreslast, auf die Monatslast und auf die Monatsspitze, jeweils Wärmestrom je Meter mal "
            "ein thermischer Widerstand des Untergrunds aus der g-Funktion des Feldes, plus den Abfall im Bohrloch:"))
        st.latex(r"T_f = T_g - q_y R_y - q_m R_m - q_h R_h - q_h R_b")
        st.markdown(L(
            "The sizing changes the length until the lowest (or highest) T_f just reaches the limit. The first and "
            "the last year are both checked, because the ground keeps changing for decades.",
            "Die Auslegung ändert die Länge, bis das niedrigste (oder höchste) T_f gerade die Grenze erreicht. Das "
            "erste und das letzte Jahr werden beide geprüft, weil sich der Untergrund über Jahrzehnte verändert."))
        source_line((1, 3, 2, 12))
    term_popovers(("imbalance", "Rb", "gfunction", "limits", "sizing_method"))


# ---------------------------------------------------------------- tabs: introduction, glossary, literature

def _done() -> set[int]:
    return st.session_state.setdefault("learn_done", set())


def introduction_tab() -> None:
    inject_css()
    done = _done()
    head, prog = st.columns([3, 1], vertical_alignment="center")
    with head:
        st.markdown("#### " + t("Introduction for new colleagues"))
        st.caption(t("{n} short modules along the input steps, about {h:.0f} hours in total. Each one explains, lets "
                     "you try it on a practice project, and lists where to read more. Progress is kept until the "
                     "page is reloaded.", n=len(modules.MODULES), h=modules.TOTAL_MINUTES / 60))
    with prog:
        st.metric(t("Your progress"), f"{len(done)} / {len(modules.MODULES)}")
        st.progress(len(done) / len(modules.MODULES))
    names = {m.number: f"{m.number} · {m.title}" + (" ✓" if m.number in done else "") for m in modules.MODULES}
    current = st.segmented_control(t("Module"), list(names), format_func=names.get, default=0, required=True,
                                   key="learn_module", label_visibility="collapsed")
    module(modules.BY_NUMBER[current])


def module(m: modules.Module) -> None:
    done = _done()
    with st.container(border=True):
        meta = [t("{n} min", n=m.minutes)]
        if m.exercises:
            meta.append(t("{n} exercises", n=len(m.exercises)) if len(m.exercises) > 1 else t("1 exercise"))
        meta.append(t("{n} sources", n=len(m.sources)))
        st.markdown(f"### {m.number} · {m.title}")
        st.html(f"<div class='modmeta'>{html.escape(' · '.join(meta))}</div>")
        st.markdown(m.body)
        for key in m.exercises:
            EXERCISES[key]()
        if m.question is not None:
            quiz(m)
        term_popovers(m.terms)
        source_line(m.sources, t("Read more:"))
        if m.number in done:
            st.success(t("Module done."), icon=":material/check_circle:")
        elif st.button(t("Mark this module as done"), icon=":material/check:", key=f"learn_done.{m.number}"):
            done.add(m.number)
            st.rerun()


def quiz(m: modules.Module) -> None:
    q = m.question
    st.markdown("**" + t("Check yourself") + ":** " + q.text)
    pick = st.radio(t("Answer"), range(len(q.choices)), format_func=lambda i: q.choices[i], index=None,
                    key=f"learn_quiz.{m.number}", label_visibility="collapsed")
    if pick is not None:
        box = "okbox" if pick == q.answer else "nobox"
        lead = t("Right.") if pick == q.answer else t("Not quite.")
        st.html(f"<div class='{box}'><b>{html.escape(lead)}</b> {html.escape(q.why)}</div>")


def glossary_tab() -> None:
    st.markdown("#### " + t("Glossary"))
    st.caption(t("The technical terms used in the labels, with symbol, typical values and sources."))
    find = st.text_input(t("Search"), placeholder=t("e.g. borehole resistance"), key="learn_find",
                         label_visibility="collapsed", icon=":material/search:").strip().lower()
    for term in sorted(glossary.TERMS, key=lambda x: x.name.lower()):
        if find and find not in (term.name + " " + term.text + " " + term.symbol).lower():
            continue
        with st.container(border=True):
            st.markdown(f"**{term.name}**" + (f" · `{term.symbol}`" if term.symbol else ""))
            st.markdown(term.text)
            refs = " · ".join(f"[[{n}]]({sources.get(n).url}) {sources.get(n).short}" for n in term.sources)
            st.caption(f":material/menu_book: {refs} · " + t("Module {n}: {title}", n=term.module,
                                          title=modules.BY_NUMBER[term.module].title))


def literature_table(module_filter: int | None = None, free_only: bool = False) -> None:
    rows = []
    for s in sources.SOURCES:
        if module_filter is not None and module_filter not in s.modules or free_only and not s.free:
            continue
        access = t("free") if s.free else t("paid · ask the library")
        rows.append(f"| [{s.number}] | **[{s.title}]({s.url})**<br>{s.authors} · {s.venue} · {s.year} · {s.language}"
                    f" | {s.why} | {', '.join(map(str, s.modules))} | {access} |")
    if not rows:
        st.info(t("No source matches the filter."))
        return
    st.markdown(f"| | {t('Title')} | {t('Why read it')} | {t('Modules')} | {t('Access')} |\n"
                "|---|---|---|---|---|\n" + "\n".join(rows), unsafe_allow_html=True)


def literature_tab() -> None:
    st.markdown("#### " + t("Literature and sources"))
    st.caption(t("One numbered list for the whole app: a number like [4] in a card or the glossary is the entry "
                 "here. {free} of {n} are free to read online. Links checked on {date}.",
                 free=sum(s.free for s in sources.SOURCES), n=len(sources.SOURCES), date=sources.CHECKED))
    with st.container(horizontal=True, vertical_alignment="bottom"):
        names = {None: t("All modules"), **{m.number: f"{m.number} · {m.title}" for m in modules.MODULES}}
        pick = st.selectbox(t("Module"), list(names), format_func=names.get, key="learn_lit_module", width=260)
        free = st.toggle(t("Free only"), key="learn_lit_free")
        st.download_button(t("List (text)"), sources.plain_list().encode(), "ghetool-literature.txt", "text/plain",
                           icon=":material/download:", on_click="ignore")
        st.download_button("BibTeX", sources.bibtex().encode(), "ghetool-literature.bib", "application/x-bibtex",
                           icon=":material/download:", on_click="ignore")
    literature_table(pick, free)


def tabs(page) -> None:
    """The three Learn tabs at the end of the steps (labels in ghe_web/page/steps.py), only in Learn mode."""
    if not page.learn:
        return
    with page.step_tabs[page.steps["learn_intro"]]:
        introduction_tab()
    with page.step_tabs[page.steps["learn_glossary"]]:
        glossary_tab()
    with page.step_tabs[page.steps["learn_literature"]]:
        literature_tab()


def menu_button() -> None:
    """In the menu ☰, in every mode: the literature list without switching to Learn."""
    if st.button(t("Literature and sources"), icon=":material/menu_book:", width="stretch", key="menu_literature"):
        _literature_dialog()


@st.dialog(" ", width="large")
def _literature_dialog() -> None:
    literature_tab()


# ---------------------------------------------------------------- exercises

@st.cache_resource(show_spinner=False)
def _cached(name: str):
    return getattr(exercises, name)()


def _line_chart(df: pd.DataFrame, x_title: str, marks: list[tuple[float, float, str, str]], guess=None) -> alt.Chart:
    data = df.dropna()
    base = alt.Chart(data).encode(x=alt.X("Value:Q", title=x_title, axis=alt.Axis(tickCount=8)),
                                  y=alt.Y("Length:Q", title=t("Required length [m]"), scale=alt.Scale(zero=False)))
    layers = [base.mark_line(color=ACCENT, strokeWidth=3), base.mark_circle(color=ACCENT, size=40)]
    if guess is not None:
        layers.append(alt.Chart(guess).mark_line(color=GREY, strokeDash=[6, 5], strokeWidth=2).encode(
            x="Value:Q", y="Length:Q"))
    pts = pd.DataFrame([{"Value": x, "Length": y, "Label": label, "Colour": c} for x, y, label, c in marks])
    layers.append(alt.Chart(pts).mark_point(size=160, filled=True, opacity=1).encode(
        x="Value:Q", y="Length:Q", color=alt.Color("Colour:N", scale=None)))
    layers.append(alt.Chart(pts).mark_text(dy=-14, fontWeight="bold").encode(x="Value:Q", y="Length:Q",
                                                                             text="Label:N"))
    return alt.layer(*layers).properties(height=280)


def _predict(key: str, question: str, options: list[str], right: int, compute, explain_right) -> None:
    """A "predict, then check" exercise: pick an answer, then the app sizes and shows the curve."""
    with st.container(border=True):
        st.html(f"<div class='learnhead'>{ui.icon('edit')} {html.escape(t('Try it · predict first'))}</div>")
        st.markdown(question)
        pick = st.radio(t("Your guess"), range(len(options)), format_func=lambda i: options[i], index=None,
                        key=f"learn_guess.{key}", label_visibility="collapsed")
        if st.button(t("Size it and check"), icon=":material/play_arrow:", key=f"learn_check.{key}",
                     disabled=pick is None, type="primary"):
            st.session_state[f"learn_checked.{key}"] = True
        if st.session_state.get(f"learn_checked.{key}") and pick is not None:
            with st.spinner(t("Sizing the practice project for every value...")):
                chart, text = compute()
            ok = pick == right
            st.html(f"<div class='{'okbox' if ok else 'nobox'}'><b>{html.escape(t('Right.') if ok else t('Not quite.'))}"
                    f"</b> {_md(text)}</div>")
            ui.show_chart(chart)
            st.markdown(explain_right)


def ex_predict_ks() -> None:
    def compute():
        df = _cached("ks_sweep")
        base = float(df.loc[np.isclose(df["Value"], 2.0), "Length"].iloc[0])
        high = float(df.loc[np.isclose(df["Value"], 4.0), "Length"].iloc[0])
        guess = pd.DataFrame({"Value": np.linspace(1.3, 4.0, 30)})
        guess["Length"] = base * 2.0 / guess["Value"]
        chart = _line_chart(df, t("Ground thermal conductivity [W/(m·K)]"),
                            [(2.0, base, fmt("{x:.1f} m", x=base), "#13294b"),
                             (4.0, high, fmt("{x:.1f} m", x=high), "#16a34a")], guess)
        return chart, fmt(L("**{p:+.0f} %**: {a:.1f} m → {b:.1f} m. Dashed: what halving would look like.",
                            "**{p:+.0f} %**: {a:.1f} m → {b:.1f} m. Gestrichelt: so sähe Halbieren aus."),
                          p=(high / base - 1) * 100, a=base, b=high)
    _predict("ks", L("The practice field needs a certain length with λ = 2.0 W/(m·K). What if the ground conducted "
                     "heat **twice as well** (4.0 W/(m·K))?",
                     "Das Übungsfeld braucht bei λ = 2,0 W/(m·K) eine bestimmte Länge. Was, wenn der Untergrund "
                     "Wärme **doppelt so gut** leiten würde (4,0 W/(m·K))?"),
             [L("It halves (−50 %)", "Sie halbiert sich (−50 %)"),
              L("About one third shorter", "Etwa ein Drittel kürzer"),
              L("About 10 % shorter", "Etwa 10 % kürzer"), L("It does not change", "Sie ändert sich nicht")], 1,
             compute,
             L("**Why not half?** Only the temperature drop *in the ground* depends on λ. The drop inside the borehole "
               "(R_b × heat flow) and the fixed limit do not, so the gain is smaller than the ratio.",
               "**Warum nicht die Hälfte?** Nur der Temperaturabfall *im Untergrund* hängt von λ ab. Der Abfall im "
               "Bohrloch (R_b × Wärmestrom) und die feste Grenze nicht, darum ist der Gewinn kleiner als das "
               "Verhältnis."))


def ex_predict_spacing() -> None:
    def compute():
        df = _cached("spacing_sweep")
        a = float(df.loc[np.isclose(df["Value"], 3.0), "Length"].iloc[0])
        b = float(df.loc[np.isclose(df["Value"], 6.0), "Length"].iloc[0])
        c = float(df.loc[np.isclose(df["Value"], 15.0), "Length"].iloc[0])
        chart = _line_chart(df, t("Borehole spacing [m]"),
                            [(6.0, b, fmt("{x:.1f} m", x=b), "#13294b"), (3.0, a, fmt("{x:.1f} m", x=a), WARM)])
        return chart, fmt(L("6 m → 3 m: **{p:+.0f} %** ({b:.1f} m → {a:.1f} m). Even 15 m only saves {s:.0f} %.",
                            "6 m → 3 m: **{p:+.0f} %** ({b:.1f} m → {a:.1f} m). Selbst 15 m sparen nur {s:.0f} %."),
                          p=(a / b - 1) * 100, a=a, b=b, s=(1 - c / b) * 100)
    _predict("spacing", L("The 6 practice boreholes are 6 m apart. The site is tight: what does **3 m** spacing do to "
                          "the length of each borehole?",
                          "Die 6 Übungssonden haben 6 m Abstand. Das Grundstück ist eng: was machen **3 m** Abstand "
                          "mit der Länge jeder Sonde?"),
             [L("Nothing, the boreholes don't interact", "Nichts, die Sonden beeinflussen sich nicht"),
              L("About 10 % longer", "Etwa 10 % länger"), L("About twice as long", "Etwa doppelt so lang")], 1,
             compute,
             L("For a small field the effect is moderate, because each borehole still has open ground on most sides. "
               "In large, compact fields it grows strongly over the years: that is what the g-function captures.",
               "Bei einem kleinen Feld ist der Effekt mäßig, weil jede Sonde noch auf den meisten Seiten freien "
               "Untergrund hat. In großen, kompakten Feldern wächst er über die Jahre stark: genau das bildet die "
               "g-Funktion ab."))


def ex_ground_years() -> None:
    with st.container(border=True):
        st.html(f"<div class='learnhead'>{ui.icon('edit')} {html.escape(t('Try it · watch the ground'))}</div>")
        st.markdown(L("The practice field, **same length**, once with summer cooling and once with heating only. "
                      "Pick a year.",
                      "Das Übungsfeld mit **gleicher Länge**, einmal mit Sommerkühlung und einmal nur mit Heizen. "
                      "Wählen Sie ein Jahr."))
        with st.spinner(t("Calculating 50 years for both cases...")):
            data = _cached("ground_years")
        year = st.segmented_control(t("Year"), [5, 25, 50], default=50, required=True, key="learn_year",
                                    format_func=lambda n: t("after {n} years", n=n))
        maps = {case: data["cases"][case]["maps"][year] for case in ("heating", "cooling")}
        # one colour scale for both cases and every year, so the maps compare
        end = [data["cases"][c]["maps"][50]["table"]["Change"] for c in ("heating", "cooling")]
        scale = (min(float(x.min()) for x in end), max(float(x.max()) for x in end))
        cols = st.columns(2)
        for col, case, title in zip(cols, ("heating", "cooling"), (t("Heating only"), t("Heating and summer cooling"))):
            with col:
                st.markdown(f"**{title}**")
                ui.show_chart(result_charts.ground_map_chart({**maps[case], "scale": scale},
                                                     size=260 if ui.is_phone() else 400), width="content")
                st.caption(t("Coldest point {x:.1f} K after {n} years", x=float(maps[case]["table"]["Change"].min()),
                             n=year))
        rows = []
        for case, title in (("heating", t("Heating only")), ("cooling", t("Heating and summer cooling"))):
            y = data["cases"][case]["yearly"]
            rows += [{"Year": int(a), "Lowest": float(b), "Case": title} for a, b in zip(y["Year"], y["Lowest"])]
        df = pd.DataFrame(rows)
        lines = alt.Chart(df).mark_line(strokeWidth=3).encode(
            x=alt.X("Year:Q", title=t("Year")), y=alt.Y("Lowest:Q", title=t("Lowest fluid temperature [°C]")),
            color=alt.Color("Case:N", title=None,
                            scale=alt.Scale(domain=[t("Heating only"), t("Heating and summer cooling")],
                                            range=[COLD, WARM]),
                            legend=alt.Legend(orient="top", labelLimit=300)))
        rule = alt.Chart(pd.DataFrame({"y": [0.0]})).mark_rule(strokeDash=[6, 4], color=COLD).encode(y="y:Q")
        ui.show_chart((lines + rule).properties(height=230))
        low = float(data["cases"]["heating"]["yearly"]["Lowest"].min())
        st.markdown(fmt(L("**What do you see?** Without cooling the ground keeps losing heat; the fluid ends at "
                          "**{low:.1f} °C**, below the limit. Putting the summer heat back (regeneration) keeps it at "
                          "the limit. To stay within the limit without cooling, the boreholes would need "
                          "**{l0:.0f} m** instead of {l:.0f} m.",
                          "**Was sehen Sie?** Ohne Kühlung verliert der Untergrund weiter Wärme; das Fluid endet bei "
                          "**{low:.1f} °C**, unter der Grenze. Die Sommerwärme zurückzugeben (Regeneration) hält es an "
                          "der Grenze. Um ohne Kühlung in der Grenze zu bleiben, bräuchten die Sonden **{l0:.0f} m** "
                          "statt {l:.0f} m."), low=low, l0=data["length_without"], l=data["length"]))


def ex_inside_borehole() -> None:
    with st.container(border=True):
        st.html(f"<div class='learnhead'>{ui.icon('edit')} {html.escape(t('Try it · inside the borehole'))}</div>")
        with st.spinner(t("Sizing the practice project...")):
            data = _cached("borehole_experiments")
        parts = data["parts"]
        if parts:
            df = pd.DataFrame([{"Part": name, "R": r, "K": r * (data["q_peak"] or 0)} for name, r in parts])
            df["Order"] = range(len(df))
            # one bar per part of R_b, with its share in K at the heating peak (plain HTML: three rows)
            top = float(df["R"].max()) or 1.0
            rows = "".join(
                f"<div class='rbrow'><span>{html.escape(name)}</span><div><i style='width:{r / top * 100:.1f}%'></i>"
                f"</div><b>{html.escape(fmt('{r:.3f} m·K/W · {k:.1f} K', r=r, k=k))}</b></div>"
                for name, r, k in zip(df["Part"], df["R"], df["K"]))
            st.html(f"<div class='rbparts'>{rows}</div>")
            st.caption(t("R_b = {rb:.3f} m·K/W, split approximately. At the heating peak ({q:.0f} W/m) the fluid is "
                         "{k:.1f} K colder than the borehole wall.", rb=data["Rb"], q=data["q_peak"] or 0,
                         k=data["Rb"] * (data["q_peak"] or 0)))
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**" + t("Grout") + "**")
            g = data["grout"].rename(columns={"Value": t("Grout [W/(m·K)]"), "Rb": "R_b [m·K/W]",
                                              "Length": t("Length [m]")})
            st.dataframe(g.round({"R_b [m·K/W]": 3, t("Length [m]"): 1}), hide_index=True, width="stretch")
        with c2:
            st.markdown("**" + t("Flow per borehole") + "**")
            f = data["flow"].assign(Re=data["flow"]["Re"].round(0)).rename(columns={
                "Value": t("Flow [kg/s]"), "Rb": "R_b [m·K/W]", "Length": t("Length [m]")})
            st.dataframe(f.round({"R_b [m·K/W]": 3, t("Length [m]"): 1}), hide_index=True, width="stretch")
        st.markdown(L("A standard bentonite grout or laminar flow (Re below about 2300) makes R_b and the length "
                      "jump. The grout is usually the largest part of R_b.",
                      "Ein Standard-Bentonit oder laminare Strömung (Re unter etwa 2300) lassen R_b und die Länge "
                      "springen. Die Verfüllung ist meist der größte Teil von R_b."))


EXERCISES = {"predict_ks": ex_predict_ks, "predict_spacing": ex_predict_spacing, "ground_years": ex_ground_years,
             "inside_borehole": ex_inside_borehole}
