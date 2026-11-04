"""Overview: the temperature chart and the key results in two columns."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, key, limits = ctx.result, ctx.key, ctx.limits
    if result.hourly_basis:  # the hourly result is what the limits were checked against
        figure(plots.hourly_band_chart(result.hourly_temperatures, limits),
               t("Daily range of the hourly average fluid temperature. Dashed: your limits."))
    else:
        figure(plots.temperature_chart(result.temperatures, limits), TEMPERATURE_CAPTION(),
               export.monthly_temperatures(result).round(3))
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



register(ResultView("overview", "Overview", 10, render))
