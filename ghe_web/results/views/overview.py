"""Overview: the temperature chart and the key results in two columns."""
from __future__ import annotations

import streamlit as st

from ghe_web.charts import result_charts
from ghe_web.downloads import excel
from ghe_web.i18n import t
from ghe_web.results.common import TEMPERATURE_CAPTION, figure, key_table
from ghe_web.results.registry import Ctx, ResultView, hidden, register


def render(ctx: Ctx) -> None:
    result, key, limits = ctx.result, ctx.key, ctx.limits
    if result.hourly_basis:  # the hourly result is what the limits were checked against
        figure(result_charts.hourly_band_chart(result.hourly_temperatures, limits),
               t("Daily range of the hourly average fluid temperature. Dashed: your limits."))
    else:
        figure(result_charts.temperature_chart(result.temperatures, limits), TEMPERATURE_CAPTION(),
               excel.monthly_temperatures(result).round(3))
    # spread the groups over two columns so both end at about the same height
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



# Not shown for now (theo, 2026-11-04): the temperatures and the key figures are on the results sheet.
register(ResultView("overview", "Overview", 10, render, available=hidden))
