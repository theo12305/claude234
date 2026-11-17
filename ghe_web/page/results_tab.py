"""The 📊 Results tab and the 🔬 Further analysis tab of borehole heat exchangers. The result views themselves are
plug-ins in ghe_web/results."""
from __future__ import annotations

import functools
import html

import streamlit as st

from ghe_web import results
from ghe_web.core import analysis, checks, model
from ghe_web.i18n import t
from ghe_web.page import calculation, design_check, project
from ghe_web.page.state import Page
from ghe_web.results import registry as results_registry
from ghe_web.results import sheet as results_sheet
from ghe_web.results import summary as results_summary
from ghe_web.results.cache import cached_size


def draw(page: Page, found_checks: list[checks.Check]) -> None:
    """The results sheet: the answer card, then every result view switched on, then the downloads."""
    action = calculation.action(page)
    ctx = None
    if "result_json" in st.session_state:
        sized_json = st.session_state.result_json
        sized_inputs = model.from_json(sized_json)[1]
        result = cached_size(sized_json)
        ctx = results.Ctx(result=result, key=analysis.key_results(result, sized_inputs), sized_inputs=sized_inputs,
                          sized_json=sized_json, current_json=page.current_json, inputs=page.inputs, name=page.name,
                          simple=page.simple, found_checks=found_checks,
                          show_design_check=functools.partial(design_check.show_design_check, page),
                          project_json=functools.partial(project.project_json, page))

    with page.step_tabs[page.steps["results"]]:
        if "calc_error" in st.session_state:
            st.error(t("The calculation failed: {error}", error=st.session_state.calc_error), icon=":material/error:")
        if ctx is None:
            st.info(t("No result yet. Check the inputs in the steps above, then press **{action}**.", action=action),
                    icon=":material/info:")
            if st.button(action, type="primary", disabled=bool(page.errors), key="results_calc"):
                calculation.calculate(page)
        else:
            if ctx.sized_json != page.current_json:
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
                st.markdown(f"<h3 class='sheethead'>{number} · {html.escape(t(view.title))}</h3>",
                            unsafe_allow_html=True)
                results_registry.render(view, ctx, number)
            st.markdown(f"<h3 class='sheethead'>{html.escape(t('Downloads'))}</h3>", unsafe_allow_html=True)
            results_registry.render(results_registry.get("export"), ctx, number + 1)

    with page.step_tabs[page.step("analysis")]:
        if ctx is None:
            st.info(t("The further analysis starts from a result. Calculate first."), icon=":material/info:")
        else:
            st.caption(t("Sensitivity, variants and a layout search, starting from the result in 📊 Results."))
            results_registry.render(results_registry.get("analysis"), ctx, 1)
