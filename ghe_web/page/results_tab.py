"""The 📊 Results tab and the 🔬 Further analysis tab of borehole heat exchangers. The result views themselves are
plug-ins in ghe_web/results."""
from __future__ import annotations

import functools
import html

import streamlit as st

from ghe_web import results
from ghe_web.core import analysis, checks, model
from ghe_web.i18n import t
from ghe_web.page import calculation, design_check, look, project
from ghe_web.page.state import Page
from ghe_web.results import registry as results_registry
from ghe_web.results import sheet as results_sheet
from ghe_web.results import summary as results_summary
from ghe_web.results.cache import cached_size


def empty_state(page: Page, action: str) -> None:
    """Results before the first calculation: what the sheet will show, and the way to it."""
    items = [("task_alt", t("Answer: number and length of the boreholes")),
             ("device_thermostat", t("Fluid temperatures over the years")), ("bolt", t("Energy balance")),
             ("layers", t("Ground and borefield")), ("download", t("PDF report and Excel"))]
    st.html(f"<div class='empty'><div class='big'>{look.icon('bar_chart')}</div><h3>{html.escape(t('No result yet'))}"
            f"</h3><div style='color:var(--muted)'>{html.escape(t('Calculate to get the results sheet:'))}</div><ul>"
            + "".join(f"<li>{look.icon(i)}{html.escape(x)}</li>" for i, x in items) + "</ul></div>")
    with st.container(horizontal=True, horizontal_alignment="center", key="empty_actions"):
        if page.step("check"):
            st.button(t("Design check first"), icon=":material/fact_check:", key="results_check",
                      on_click=design_check.open_design_check)
        if st.button(action, type="primary", disabled=bool(page.errors), key="results_calc",
                     icon=":material/play_arrow:"):
            calculation.calculate(page)


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
            empty_state(page, action)
        else:
            if ctx.sized_json != page.current_json:
                st.warning(t("The inputs changed since this result was calculated. Press **{action}** to update it.",
                             action=action), icon=":material/update:")
            sections = results_registry.sheet_views(ctx)
            shown = [view for view in sections if results_sheet.section_on(view.key)]
            with st.container(horizontal=True, key="sheetbar", gap="small"):
                look.contents_bar([("answer", t("Answer"))] + [(v.key, t(v.title)) for v in shown] +
                                  [("export", t("Downloads"))])
                results_sheet.customize(sections)
            st.html("<div id='sec-answer'></div>")
            results_summary.answer_section(ctx)
            for number, view in enumerate(shown, start=1):  # every section switched on, one below the other
                st.html(look.sheet_heading(view.key, t(view.title)))
                results_registry.render(view, ctx, number)
            st.html(look.sheet_heading("export", t("Downloads")))
            results_registry.render(results_registry.get("export"), ctx, len(shown) + 1)

    with page.step_tabs[page.step("analysis")]:
        if ctx is None:
            st.info(t("The further analysis starts from a result. Calculate first."), icon=":material/info:")
        else:
            results_registry.render(results_registry.get("analysis"), ctx, 1)
