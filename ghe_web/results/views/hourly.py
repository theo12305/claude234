"""Hourly temperatures (only for hourly loads)."""
from __future__ import annotations

from ghe_web.charts import result_charts
from ghe_web.i18n import t
from ghe_web.results import sheet
from ghe_web.results.common import figure
from ghe_web.results.registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, limits = ctx.result, ctx.limits
    style = sheet.style()
    if sheet.on("hourly_daily"):
        figure(result_charts.hourly_band_chart(result.hourly_temperatures, limits, style))
    if sheet.on("hourly_last"):
        figure(result_charts.hourly_last_year_chart(result.hourly_temperatures, limits, style),
               t("The band spans the lowest and highest fluid temperature of every 3 hours, so all peaks are "
                 "visible."))
    if sheet.on("hourly_heatmap"):
        figure(result_charts.heatmap_chart(result.hourly_temperatures),
               t("Each cell is one hour of the last year. Blue is cold, red is warm."))


register(ResultView("hourly", "Hourly", 50, render, available=lambda ctx: ctx.result.hourly_temperatures is not None))
