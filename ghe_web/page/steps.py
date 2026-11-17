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


def step_key(page: Page, label: str) -> str | None:
    """The step id of a tab label (in Simple mode the first of the steps that share the label)."""
    return next((k for k, v in page.steps.items() if v == label), None)


def next_step_button(page: Page, step: str) -> None:
    """At the bottom of each step: back to the previous one, where this step is, and on to the next one. The last
    input step calculates and opens the results."""
    index = page.step_names.index(step)
    following = page.step_names[index + 1]
    n_inputs = page.step_names.index(page.steps.get("check") or page.steps["results"])
    with st.container(horizontal=True, vertical_alignment="center", key=f"next.{index}"):
        if index > 0:
            back = step_key(page, page.step_names[index - 1])
            st.button(t("Back"), icon=":material/arrow_back:", key=f"back.{index}",
                      on_click=lambda: st.session_state.update(goto_step=back))
        st.space("stretch")
        st.html(f"<div class='stepof'>{t('Step {i} of {n}', i=index + 1, n=n_inputs)}</div>")
        if following == page.steps["results"]:
            st.button(t("Calculate and show the results"), type="primary", icon=":material/play_arrow:",
                      on_click=lambda: st.session_state.update(calc_requested=True))
        else:
            key_ = next(k for k, v in page.steps.items() if v == following)
            st.button(t("Next: {step}", step=following), icon=":material/arrow_forward:", type="primary",
                      on_click=lambda: st.session_state.update(goto_step=key_))


def status_css(page: Page, found_checks: list) -> None:
    """The state of each step on its tab: a green tick when it was opened and is fine, an amber warning, a red mark
    for an input error or problem; Results and Further analysis greyed out until there is a result. A thin bar under
    the tabs shows how many input steps were opened. Drawn with CSS on the tabs, so the tab labels (which are also
    the ids of the open tab) stay the same."""
    from ghe_web.core import checks
    visited = st.session_state.setdefault("visited_steps", {"Site"})
    open_key = step_key(page, st.session_state.get("step") or page.steps["Site"])
    if open_key:
        visited.add(open_key)
    level: dict[str, str] = {}
    rank = {"ok": 0, "warn": 1, "bad": 2}

    def mark(section_key: str, kind: str) -> None:
        label = page.steps[section_step_key(page, section_key)]
        if rank[kind] > rank.get(level.get(label, "ok"), 0) or label not in level:
            level[label] = kind
    for c in found_checks:
        if c.section and c.level != checks.FINE:
            mark(c.section, "bad" if c.level == checks.PROBLEM else "warn")
    for key in page.errors:
        mark(key, "bad")
    no_result = "result_json" not in st.session_state
    inputs = page.step_names[1:page.step_names.index(page.steps.get("check") or page.steps["results"])]
    rules, done = [], 0
    for i, label in enumerate(page.step_names, start=1):
        key = step_key(page, label)
        tab = f'.st-key-step [role="tab"]:nth-of-type({i})'
        kind = level.get(label)
        if kind is None and label in inputs and key in visited:
            kind = "ok"
        if label in inputs and kind in ("ok", "warn"):
            done += 1
        if key in ("results", "analysis") and no_result:
            rules.append(f'{tab}:not([aria-selected="true"]) {{opacity: .5;}}')
        elif key == "check" and found_checks:
            kind = "bad" if any(c.level == checks.PROBLEM for c in found_checks) else \
                "warn" if any(c.level == checks.WARNING for c in found_checks) else "ok"
        if kind:
            rules.append(f"{tab} p::after {{{_STATUS[kind]}}}")
    share = done / len(inputs) if inputs else 0
    rules.append(f'.st-key-step [role="tablist"] {{background: linear-gradient(var(--accent), var(--accent)) '
                 f'left bottom / {share * 100:.0f}% 3px no-repeat;}}')
    st.html("<style>" + "\n".join(rules) + "</style>")


_STATUS = {kind: f'content: "{name}"; color: {colour}; font-family: "Material Symbols Rounded"; font-size: 1.05rem; '
                 f'margin-left: 6px; vertical-align: -3px; font-variation-settings: "FILL" 1;'
           for kind, name, colour in (("ok", "check_circle", "#16a34a"), ("warn", "error", "#d97706"),
                                      ("bad", "cancel", "#dc2626"))}
