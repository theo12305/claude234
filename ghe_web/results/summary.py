"""The top of the results: the answer card with the key tiles and quick downloads, and the one-page results of Simple mode."""
from __future__ import annotations

import streamlit as st

from ghe_web import i18n
from ghe_web.core import checks
from ghe_web.downloads import excel, pdf_report
from ghe_web.i18n import fmt, t
from ghe_web.page import look
from ghe_web.results import sheet
from ghe_web.results.cache import *  # noqa: F403 (the cached calculations)
from ghe_web.results.common import in_language, key_table
from ghe_web.results.registry import Ctx, extra_tables


def answer_section(ctx: Ctx) -> None:
    """The answer first: a card with the design and the design check, the key figures as tiles, the warnings and the
    most used downloads."""
    result, key, sized_inputs, limits, sized_json = ctx.result, ctx.key, ctx.sized_inputs, ctx.limits, ctx.sized_json
    name, lang, found_checks = ctx.name, i18n.language(), ctx.found_checks
    ui_mode = "simple" if ctx.simple else "expert"
    project_json = ctx.project_json
    choice = sheet.choice()
    years = sized_inputs["load"].values["simulation_period"]
    vals = key.values
    t_lo, t_hi = (round(vals[k], 1) + 0.0 for k in ("t_min", "t_max"))  # + 0.0 avoids "-0.0"
    if result.sizing_method == "check":
        ok = bool(vals.get("passes"))
        lead = t("Check of the given length")
        big = t("{n} boreholes × {length:.1f} m", n=result.number_of_boreholes, length=result.borehole_length)
        sub = (t("The given length of {length:.0f} m keeps the fluid within the limits.", length=result.borehole_length)
               if ok else t("The given length of {length:.0f} m does not keep the fluid within the limits.",
                            length=result.borehole_length))
    else:
        ok = True
        lead = t("Answer")
        big = t("{n} boreholes × {length:.1f} m", n=result.number_of_boreholes, length=result.borehole_length)
        if abs(vals["margin_cold"] - vals["margin_warm"]) < 0.3:
            decides = t("heating and cooling need about the same length")
        elif vals["margin_cold"] < vals["margin_warm"]:
            decides = t("heating decides the length")
        else:
            decides = t("cooling decides the length")
        sub = t("{total:,.0f} m drilled · fluid between {lo:.1f} and {hi:.1f} °C over {years} years · {decides} "
                "({method})", total=result.total_length, lo=t_lo, hi=t_hi, years=years, decides=decides,
                method=t(pdf_report.METHOD[result.sizing_method]))
    n = checks.counts(found_checks)
    chip_items = [("bad", t("{n} problem(s)", n=n[checks.PROBLEM]))] if n[checks.PROBLEM] else []
    if n[checks.WARNING]:
        chip_items.append(("warn", t("{n} warning(s)", n=n[checks.WARNING])))
    chip_items.append(("ok", t("{n} fine", n=n[checks.FINE])))
    look.answer_card(ok, lead, big, sub, chip_items)

    def margin_note(margin: float, limit: float) -> str:
        if abs(margin) < 0.05:  # sizing stops within a few hundredths of a kelvin of the limit
            return t("limit {x:g} °C", x=limit) + " · " + t("at the limit")
        return t("limit {x:g} °C", x=limit) + " · " + (t("{x:+.1f} K margin", x=margin) if margin > 0 else
                                                       t("{x:.1f} K beyond the limit", x=-margin))
    items = [
        (":material/straighten: " + (t("Borehole length") if result.sizing_method == "check" else t("Required borehole length")),
         fmt("{x:.1f} m", x=result.borehole_length), t("{n} boreholes", n=result.number_of_boreholes), ""),
        (":material/functions: " + t("Total borehole length"), fmt("{x:,.0f} m", x=result.total_length),
         t("{n} boreholes", n=result.number_of_boreholes), ""),
        (":material/ac_unit: " + t("Lowest fluid temperature"), fmt("{x:.1f} °C", x=t_lo), margin_note(vals["margin_cold"],
                                                                                       limits["T_min"]), "cold"),
        (":material/local_fire_department: " + t("Highest fluid temperature"), fmt("{x:.1f} °C", x=t_hi), margin_note(vals["margin_warm"],
                                                                                        limits["T_max"]), "warm"),
        (":material/adjust: " + t("Borehole thermal resistance"), fmt("{x:.3f} m·K/W", x=result.borehole_resistance),
         t("effective Rb"), ""),
    ]
    if "spf_heating" in vals:
        items.append((":material/bolt: " + t("Seasonal performance factor (SPF), heating"), fmt("{x:.2f}", x=vals["spf_heating"]),
                      t("heat pump electricity {x:,.1f} MWh per year", x=vals.get("electricity_mwh", 0.0)), ""))
    if "dp_kpa" in vals:
        items.append((":material/water_drop: " + t("Pressure drop per borehole"), fmt("{x:.1f} kPa", x=vals["dp_kpa"]),
                      t("{w:,.0f} W electrical", w=vals["pump_electric_w"]), ""))
    if sheet.on("tiles"):
        look.tiles(items if ui_mode == "expert" else items[:4])
    if sheet.on("key_table"):
        key_results_table(key)
    if sheet.on("warnings"):
        for w in key.warnings:
            st.warning(w, icon=":material/warning:")
    stem = name.strip() or "ghetool-project"
    # Simple: one Download button with everything in it; Expert: the buttons in a row
    with st.popover(t("Download"), icon=":material/download:") if ui_mode != "expert" else \
            st.container(horizontal=True, gap="small", key="quick_downloads"):
        st.download_button(t("PDF summary"), lambda: i18n.call_in(
            lang, pdf_report.make_pdf, result, sized_inputs, name,
            pdf_report.ReportOptions(kind="summary", title=name.strip(), sheet=choice), {}),
            f"{stem}_summary.pdf", "application/pdf", icon=":material/picture_as_pdf:", on_click="ignore")
        st.download_button(t("Excel"), in_language(excel.excel_workbook, result, sized_inputs, name,
                                                   extra_tables(ctx)),
                           f"{stem}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           icon=":material/table_view:", on_click="ignore")
        st.download_button(t("Save project"), lambda: project_json().encode(),
                           f"{stem}.json", "application/json", icon=":material/save:", key="quick_save", on_click="ignore")
        st.caption(t("Full report and more downloads at the end of the page."))


def key_results_table(key) -> None:
    """The key results in groups, spread over two columns so both end at about the same height."""
    parts, heights = ([], []), [0, 0]
    for group, rows in key.by_group().items():
        side = heights.index(min(heights))
        parts[side].append((group, rows))
        heights[side] += len(rows) + 1
    for col, part in zip(st.columns(2, gap="large"), parts):
        with col:
            for group, rows in part:
                with st.container(border=True):
                    st.markdown(f"**{group}**")
                    key_table(rows)
