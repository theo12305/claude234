"""The design check: every input and result check in one list, as a step of its own and in the results."""
from __future__ import annotations

import html

import streamlit as st

from ghe_web.core import analysis, checks
from ghe_web.i18n import t
from ghe_web.page import look, steps
from ghe_web.page.state import Page
from ghe_web.results.cache import cached_size


def design_checks(page: Page) -> list[checks.Check]:
    """Input checks, plus the result checks when the current inputs have been calculated."""
    found = checks.input_checks(page.inputs)
    if not page.errors and st.session_state.get("result_json") == page.current_json:
        res = cached_size(page.current_json)
        found += checks.result_checks(res, page.inputs, analysis.key_results(res, page.inputs))
    order = {checks.PROBLEM: 0, checks.WARNING: 1, checks.FINE: 2}
    return sorted(found, key=lambda c: order[c.level])


def open_design_check() -> None:
    """Opens the design check step."""
    st.session_state.goto_step = "check"


# level -> (CSS class, icon)
_LEVELS = {checks.PROBLEM: ("bad", "cancel"), checks.WARNING: ("warn", "error"), checks.FINE: ("ok", "check_circle")}


def show_design_check(page: Page, found: list[checks.Check], title: bool = True) -> None:
    """The checks as a summary: the counts of problems, warnings and fine checks, then the checks grouped by level,
    each with a coloured edge and a button to the step where it can be fixed."""
    if title:
        st.markdown(t("**Design check: {summary}**", summary=checks.summary(found)),
                    help=t("Every check in one place. The temperature, flow, antifreeze and balance checks appear "
                           "after a calculation."))
    n = checks.counts(found)
    names = {checks.PROBLEM: t("Problems"), checks.WARNING: t("Warnings"), checks.FINE: t("Fine")}
    st.html("<div class='ccounts'>" + "".join(
        f"<div class='ccount lv-{cls}{' zero' if not n[level] else ''}'>{look.icon(name)}<div><div class='v'>"
        f"{n[level]}</div><div class='l'>{html.escape(names[level])}</div></div></div>"
        for level, (cls, name) in _LEVELS.items()) + "</div>")
    for level, (cls, name) in _LEVELS.items():
        group_checks = [(i, c) for i, c in enumerate(found) if c.level == level]
        if not group_checks:
            continue
        st.html(f"<div class='cgroup lv-{cls}'>{look.icon(name)}{html.escape(names[level])}</div>")
        for i, check in group_checks:
            with st.container(border=True, key=f"chk_{cls}_{i}"):
                text_col, button_col = st.columns([4, 1.6], vertical_alignment="center")
                text_col.markdown(f"**{check.title}**  \n{check.detail}")
                if check.section and check.level != checks.FINE:
                    step = steps.section_step_key(page, check.section)
                    button_col.button(t("Go to {step}", step=page.steps[step]), key=f"check.goto.{i}",
                                      width="stretch", on_click=lambda step=step: st.session_state.update(goto_step=step))


def tab(page: Page, found: list[checks.Check]) -> None:
    """The design check step: the list, and the button that calculates and opens the results."""
    with page.step_tabs[page.step("check")]:
        st.markdown(look.section_heading("checks", t("Design check")), unsafe_allow_html=True, help=t(
            "Every input check in one place; after a calculation also the temperature, flow, antifreeze and balance "
            "checks. Confirm to calculate and open the results."))
        show_design_check(page, found, title=False)
        if page.errors:
            st.error(t("Correct the inputs marked in red first."), icon=":material/error:")
        with st.container(horizontal=True, horizontal_alignment="right", key="check_confirm_row"):
            st.button(t("Confirm and calculate"), type="primary", icon=":material/check:", disabled=bool(page.errors),
                      key="check_confirm", on_click=lambda: st.session_state.update(calc_requested=True))


