"""Export: Excel, PDF report, zip and CSV downloads."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from .. import sheet
from ..registry import Ctx, ResultView, register


REPORT_KINDS = {"full": "Full report", "summary": "One-page summary"}


def report_settings(sized_json: str, stem: str) -> tuple[report.ReportOptions, dict]:
    """Report settings in an expander. Text fields keep their values while the page is open."""
    with st.expander(t("Report settings: type, title, company, client, logo, introduction and conclusion"),
                     icon=":material/edit_document:"):
        kind = st.selectbox(t("Report type"), list(REPORT_KINDS), key="rep_kind",
                            format_func=lambda k: t(REPORT_KINDS[k]))
        c1, c2 = st.columns(2)
        title = c1.text_input(t("Title"), key="rep_title", placeholder=stem)
        subtitle = c2.text_input(t("Subtitle"), key="rep_subtitle",
                                 placeholder=t("e.g. Borefield sizing, design phase"))
        author = c1.text_input(t("Author"), key="rep_author")
        company = c2.text_input(t("Company"), key="rep_company")
        client = c1.text_input(t("Client"), key="rep_client")
        logo = c2.file_uploader(t("Logo (PNG or JPEG)"), type=["png", "jpg", "jpeg"], key="rep_logo")
        intro = st.text_area(t("Introduction"), key="rep_intro", height=90,
                             placeholder=t("Project background, scope of the calculation..."))
        conclusion = st.text_area(t("Conclusion"), key="rep_conclusion", height=90)
        with_inputs = st.checkbox(t("Include the inputs and their drawings"), value=True, key="rep_inputs")
        st.caption(t("The charts in the report are the ones switched on under Customize the results, with the same "
                     "lines and markers."))
    choice = sheet.choice()
    options = report.ReportOptions(kind=kind, title=title, subtitle=subtitle, author=author, company=company,
                                   client=client, introduction=intro, conclusion=conclusion,
                                   logo=logo.getvalue() if logo else None, sheet=choice, inputs=with_inputs)
    extras = {"load_optimisation": load_optimisation_done(sized_json)}
    if choice["sections"].get("ground"):  # calculated for the page already, so cached
        extras["ground_map"] = cached_ground_map(sized_json)
    if choice["sections"].get("field"):
        extras["borehole_map"] = cached_borehole_map(sized_json, None)
    return options, extras



def render(ctx: Ctx) -> None:
    result, sized_inputs, sized_json, name = ctx.result, ctx.sized_inputs, ctx.sized_json, ctx.name
    lang = i18n.language()
    from ..registry import extra_tables
    stem = name.strip() or "ghetool-project"
    extra = extra_tables(ctx)
    included = ", ".join(extra) if extra else t("none yet; run them under Further analysis to include them")
    st.markdown(t("The files are made when you click, so the page stays fast. The PDF report and the Excel workbook "
                  "are in the language chosen at the top."))
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        st.markdown(t("**Excel workbook**"))
        st.caption(t("Summary, inputs, monthly and yearly temperatures, ground energy, hourly results and your "
                     "further analysis (included: {included}).", included=included))
        st.download_button(t("Download Excel (.xlsx)"), in_language(export.excel_workbook, result, sized_inputs, name,
                                                                    extra),
                           f"{stem}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           type="primary", icon=":material/table_view:", on_click="ignore")
    with c2, st.container(border=True):
        st.markdown(t("**PDF report**"))
        st.caption(t("Full report: cover page, key results, the charts of this page, inputs and drawings. One-page "
                     "summary: the design, key results and the temperature chart. Fill in the report settings below "
                     "first."))
        st.download_button(t("Download PDF"),
                           lambda: i18n.call_in(lang, report.make_pdf, result, sized_inputs, name, options,
                                                report_extras),
                           f"{stem}.pdf", "application/pdf", type="primary", icon=":material/picture_as_pdf:",
                           on_click="ignore")
    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        st.markdown(t("**Everything in one zip**"))
        st.caption(t("Excel workbook, PDF report and the project file, for archiving a design."))
        st.download_button(t("Download zip"),
                           lambda: i18n.call_in(lang, export.zip_bundle, result, sized_inputs, name, extra, options,
                                                report_extras),
                           f"{stem}.zip", "application/zip", icon=":material/folder_zip:", on_click="ignore")
    with c4, st.container(border=True):
        st.markdown(t("**CSV files**"))
        st.caption(t("Plain tables for other tools."))
        st.download_button(t("Monthly temperatures (CSV)"),
                           in_language(lambda: export.monthly_temperatures(result).to_csv(index=False).encode()),
                           f"{stem}_monthly.csv", "text/csv", icon=":material/download:", on_click="ignore")
        if result.hourly_temperatures is not None:
            st.download_button(t("Hourly temperatures (CSV)"),
                               lambda: result.hourly_temperatures.round(3).to_csv().encode(),
                               f"{stem}_hourly.csv", "text/csv", icon=":material/download:", on_click="ignore")
    # read when a download button is clicked, so it can come after the buttons on the page
    options, report_extras = report_settings(sized_json, stem)



register(ResultView("export", "Downloads", 1000, render, on_sheet=False))  # always at the end of the sheet
