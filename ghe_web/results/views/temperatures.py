"""Temperatures: over the years with the last year enlarged, the last year with supply and return, the yearly
extremes and the table. Each part can be switched on and off in "Customize the results"."""
from __future__ import annotations

import streamlit as st

from ... import analysis, export, plots
from ...i18n import t
from .. import sheet
from ..common import TEMPERATURE_CAPTION, figure
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, limits = ctx.result, ctx.limits
    style = sheet.style()
    if result.hourly_basis:
        st.info(t("These are the monthly temperatures with block peaks, shown for comparison. The sizing checked "
                  "the limits hour by hour: see **Hourly** for those temperatures."), icon=":material/info:")
    table = export.monthly_temperatures(result).round(3)
    if sheet.on("temp_years"):
        years = round(float(result.temperatures.index.max()))
        period = None
        if years > 1:
            period = st.slider(t("Years shown"), 0, years, (0, years), key="temp_period",
                               help=t("Zoom in on a part of the simulation period."))
            if tuple(period) == (0, years):
                period = None
        main = plots.temperature_chart(result.temperatures, limits, period, style)
        if sheet.on("temp_zoom"):
            left, right = st.columns([3, 1], gap="medium")
            with left:
                figure(main, TEMPERATURE_CAPTION(), table)
            with right:
                figure(plots.last_year_chart(result.temperatures, limits, compact=True, style=style),
                       t("The last year enlarged: blue, grey and red as on the left."), table.tail(12))
        else:
            figure(main, TEMPERATURE_CAPTION(), table)
    elif sheet.on("temp_zoom"):
        figure(plots.last_year_chart(result.temperatures, limits, compact=True, style=style), data=table.tail(12))
    if sheet.on("temp_last"):
        caption = t("Into the borefield = supply from the heat pump; out of the borefield = return to the heat pump.") \
            if "Into borefield (peak extraction)" in result.temperatures else None
        figure(plots.last_year_chart(result.temperatures, limits, style=style), caption, table.tail(12))
    if sheet.on("temp_extremes"):
        extremes = analysis.yearly_extremes(result)
        figure(plots.yearly_extremes_chart(extremes, limits, style),
               t("If the lowest temperature keeps falling (or the highest keeps rising) every year, the ground is out "
                 "of balance. A longer simulation period shows whether it levels off."), extremes.round(3))
    if sheet.on("temp_table"):
        st.dataframe(export.monthly_temperatures(result).round(2), hide_index=True, width="stretch", height=420)


register(ResultView("temperatures", "Temperatures", 30, render))
