"""The calculation of borehole heat exchangers and the calculate bar fixed at the bottom of the screen (status,
design check, calculate button). Groundwater wells have their own: ghe_web/wells/page.py."""
from __future__ import annotations

import streamlit as st

from ghe_web.core import checks, model
from ghe_web.i18n import t
from ghe_web.inputs import registry as input_registry
from ghe_web.page import design_check, look, steps
from ghe_web.page.state import Page
from ghe_web.results.cache import cached_size


def action(page: Page) -> str:
    """The label of the calculate button."""
    return t("Check temperatures") if page.inputs["calculation"].variant == "check" else t("Size borefield")


def calculate(page: Page) -> None:
    """Sizes the borefield of the current inputs (cached), then opens the results. GHEtool errors are shown there."""
    slow = model.temperature_dependent_cop(page.inputs) and page.inputs["load"].values.get("hourly_sizing")
    with st.spinner(t("Calculating... hourly sizing with a temperature-dependent COP takes one to two minutes.")
                    if slow else t("Calculating... hourly sizing can take up to a minute.")):
        try:
            cached_size(page.current_json)
        except Exception as exc:  # show GHEtool errors to the user instead of crashing
            st.session_state.pop("result_json", None)
            st.session_state.calc_error = str(exc)
        else:
            st.session_state.result_json = page.current_json
            st.session_state.pop("calc_error", None)
        st.session_state.goto_results = True
    st.rerun()


def run_if_requested(page: Page) -> None:
    """The button at the end of the last input step: calculate, or open the first step with an input error."""
    if st.session_state.pop("calc_requested", False):
        if page.errors:
            st.session_state.goto_step = steps.section_step_key(page, next(iter(page.errors)))
            st.rerun()
        calculate(page)


def first_error_step(page: Page) -> None:
    """Opens the step with the first input error."""
    st.session_state.goto_step = steps.section_step_key(page, next(iter(page.errors)))


def bar(page: Page, found_checks: list[checks.Check]) -> None:
    """The calculate bar: status of the result, the design check and the calculate button."""
    with page.calc_slot:
        n = checks.counts(found_checks)
        with st.container(width="stretch"):
            if page.errors:
                where = "; ".join(f"{page.section_step.get(k, '')}: {t(input_registry.get(k).label)}"
                                  for k in page.errors)
                look.calc_status("bad", t("{n} input(s) need attention", n=sum(len(m) for m in page.errors.values())),
                                 where)
            elif "calc_error" in st.session_state:
                look.calc_status("bad", t("The calculation failed"), t("Details in 📊 Results."))
            elif "result_json" in st.session_state:
                res = cached_size(st.session_state.result_json)
                last = t("{n} × {length:.1f} m, {total:,.0f} m in total", n=res.number_of_boreholes,
                         length=res.borehole_length, total=res.total_length)
                if st.session_state.result_json != page.current_json:
                    look.calc_status("warn", t("Inputs changed – results out of date"), t("Last result: {x}", x=last))
                else:
                    look.calc_status("ok", t("Result up to date"), last)
            else:
                look.calc_status("grey", t("Not calculated yet"))
        if page.errors:
            st.button(t("Show"), on_click=first_error_step, args=(page,), key="calc_goto_error",
                      icon=":material/arrow_upward:")
        check_label = " · ".join(x for x in (
            t("{n} problem(s)", n=n[checks.PROBLEM]) if n[checks.PROBLEM] else "",
            t("{n} warning(s)", n=n[checks.WARNING]) if n[checks.WARNING] else "") if x) or t("Design check")
        st.button(check_label, on_click=design_check.open_design_check, key="open_checks",
                  help=t("Open the design check"),
                  icon=":material/error:" if n[checks.PROBLEM] else ":material/warning:" if n[checks.WARNING]
                  else ":material/fact_check:")
        if st.button(action(page), type="primary", disabled=bool(page.errors), icon=":material/play_arrow:",
                     key="calc_go"):
            calculate(page)


