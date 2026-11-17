"""The design check: every input and result check in one list, as a step of its own and in the results."""
from __future__ import annotations

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


check_icons = {checks.PROBLEM: ":red[:material/cancel:]", checks.WARNING: ":orange[:material/warning:]",
               checks.FINE: ":green[:material/check_circle:]"}


def show_design_check(page: Page, found: list[checks.Check]) -> None:
    """The list of checks, each with a button to the step where it can be fixed."""
    st.markdown(t("**Design check: {summary}**", summary=checks.summary(found)))
    look.caption(t("Every check in one place. The temperature, flow, antifreeze and balance checks appear after a "
                   "calculation."))
    for i, check in enumerate(found):
        with st.container(border=True):
            text_col, button_col = st.columns([4, 1.6], vertical_alignment="center")
            text_col.markdown(f"{check_icons[check.level]} **{check.title}**  \n{check.detail}")
            if check.section and check.level != checks.FINE:
                step = steps.section_step_key(page, check.section)
                button_col.button(t("Go to {step}", step=page.steps[step]), key=f"check.goto.{i}", width="stretch",
                                  on_click=lambda step=step: st.session_state.update(goto_step=step))


def tab(page: Page, found: list[checks.Check]) -> None:
    """The design check step: the list, and the button that calculates and opens the results."""
    with page.step_tabs[page.step("check")]:
        st.markdown("##### " + t("Design check"), help=t(
            "Every input check in one place; after a calculation also the temperature, flow, antifreeze and balance "
            "checks. Confirm to calculate and open the results."))
        show_design_check(page, found)
        if page.errors:
            st.error(t("Correct the inputs marked in red first."), icon=":material/error:")
        with st.container(horizontal=True, horizontal_alignment="right", key="check_confirm_row"):
            st.button(t("Confirm and calculate"), type="primary", icon=":material/check:", disabled=bool(page.errors),
                      key="check_confirm", on_click=lambda: st.session_state.update(calc_requested=True))


