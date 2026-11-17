"""The input steps as tabs: their labels, which tab is open, the tabs themselves and the Next buttons."""
from __future__ import annotations

import streamlit as st

from ghe_web import i18n
from ghe_web.i18n import t
from ghe_web.inputs import registry as input_registry
from ghe_web.page.state import Page

# Input steps, in page order. A section with an unknown group lands in "More inputs", so new
# sections show up without changes here. The tab labels follow the language; the ids stay the same.
STEP_LABELS = {"site_plan": ":material/map: Site plan", "Site": ":material/layers: Ground & borefield", "Borehole": ":material/adjust: Borehole & fluid",
               "Loads": ":material/thermostat: Loads", "Design": ":material/tune: Limits & calculation", "more": "More inputs",
               "check": ":material/fact_check: Design check", "results": ":material/bar_chart: Results",
               "analysis": ":material/science: Further analysis"}
# The same steps for groundwater wells (open loop)
WELL_STEP_LABELS = {"site_plan": ":material/map: Site plan", "Site": ":material/layers: Ground & aquifer", "Borehole": ":material/water_pump: Wells",
                    "Loads": ":material/thermostat: Loads", "Design": ":material/tune: Limits & calculation", "more": "More inputs",
                    "results": ":material/bar_chart: Results"}

# Simple mode: the borehole, fluid and limits are part of the Loads step (same labels: the steps carry icons, not
# numbers, so nothing is renumbered)
SIMPLE_STEP_LABELS: dict[str, str] = {}
# Learn mode: three more tabs at the end (drawn by ghe_web/learn/page.py)
LEARN_LABELS = {"learn_intro": ":material/school: Introduction", "learn_glossary": ":material/dictionary: Glossary",
                "learn_literature": ":material/menu_book: Literature"}


def labels(system: str, simple: bool, learn: bool = False) -> dict[str, str]:
    """Step id -> tab label in the current language."""
    labels_ = WELL_STEP_LABELS if system == "open" else STEP_LABELS
    if simple:  # three input steps: the borehole, fluid and limits come with typical values under Loads
        # (only the labels of steps this heat source has: wells have no design check, which crashed the tabs)
        labels_ = {**labels_, **{k: v for k, v in SIMPLE_STEP_LABELS.items() if k in labels_}}
    if learn:
        labels_ = {**labels_, **LEARN_LABELS}
    steps = {k: t(v) for k, v in labels_.items()}
    if simple:
        steps["Borehole"] = steps["Design"] = steps["Loads"]
    return steps


def follow_goto(page: Page) -> None:
    """Opens the tab that a button asked for (``goto_step``, ``goto_results``). After a change of the language or
    the heat source the same tab stays open under its new label."""
    if st.session_state.pop("goto_results", False):
        st.session_state.step = page.steps["results"]
    if "goto_step" in st.session_state:
        st.session_state.step = page.steps[st.session_state.pop("goto_step")]
    if st.session_state.get("step") not in (None, *page.steps.values()):
        # the language or the heat source changed: the same tab, under its new label
        for code in i18n.LANGUAGES:
            with i18n.using(code):
                match = [k for labels in (STEP_LABELS, WELL_STEP_LABELS, SIMPLE_STEP_LABELS, LEARN_LABELS) for k, v in labels.items()
                         if t(v) == st.session_state.step]
            if match:
                st.session_state.step = page.steps[match[0]]
                break
        else:
            del st.session_state.step


def section_step_key(page: Page, section_key: str) -> str:
    """The step id of the tab a section is shown in."""
    group = input_registry.get(section_key).group
    return group if group in page.steps and group not in ("site_plan", "results") else "more"


def grouped_sections(page: Page) -> dict[str, list]:
    """Tab label -> the input sections shown in it, in page order. A section with an unknown group lands in
    "More inputs", so new sections show up without changes here."""
    grouped: dict[str, list] = {}
    for section in input_registry.sections(page.system):
        grouped.setdefault(page.steps.get(section.group, page.steps["more"]), []).append(section)
    return grouped


def make_tabs(page: Page, grouped: dict[str, list]) -> None:
    """The tabs: site plan, the input steps, then (borehole heat exchangers) the design check, the results and the
    further analysis."""
    steps = page.steps
    inputs = [steps[k] for k in ("Site", "Borehole", "Loads", "Design")] + [steps["more"]]
    page.step_names = [steps["site_plan"]] + list(dict.fromkeys(s for s in inputs if s in grouped))
    # borehole heat exchangers: confirm the design check, then the results, then the further analysis
    page.step_names += [steps.get("check"), steps["results"], steps.get("analysis")] if steps.get("check") \
        else [steps["results"]]
    page.step_names += [steps[k] for k in LEARN_LABELS if k in steps]
    page.step_tabs = dict(zip(page.step_names, st.tabs(page.step_names, default=steps["Site"], key="step",
                                                       on_change="rerun")))


def next_step_button(page: Page, step: str) -> None:
    """At the bottom of each step: go on to the next one. The last input step calculates and opens the results."""
    following = page.step_names[page.step_names.index(step) + 1]
    with st.container(horizontal=True, horizontal_alignment="right", key=f"next.{page.step_names.index(step)}"):
        if following == page.steps["results"]:
            st.button(t("Calculate and show the results"), type="primary", icon=":material/play_arrow:",
                      on_click=lambda: st.session_state.update(calc_requested=True))
        else:
            key_ = next(k for k, v in page.steps.items() if v == following)
            st.button(t("Next: {step}", step=following), icon=":material/arrow_forward:", type="primary",
                      on_click=lambda: st.session_state.update(goto_step=key_))
