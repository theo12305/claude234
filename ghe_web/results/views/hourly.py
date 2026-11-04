"""Hourly temperatures (only for hourly loads)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


HOURLY_VIEWS = {"daily": "Daily range", "last": "Last year", "heatmap": "Heat map"}


def render(ctx: Ctx) -> None:
    result, limits = ctx.result, ctx.limits
    choice = st.selectbox(t("Chart"), list(HOURLY_VIEWS), format_func=lambda k: t(HOURLY_VIEWS[k]),
                          key="hourly_view_id")
    if choice == "daily":
        figure(plots.hourly_band_chart(result.hourly_temperatures, limits))
    elif choice == "last":
        figure(plots.hourly_last_year_chart(result.hourly_temperatures, limits))
        ui.caption(t("The band spans the lowest and highest fluid temperature of every 3 hours, so all peaks are "
                     "visible."))
    else:
        figure(plots.heatmap_chart(result.hourly_temperatures))
        ui.caption(t("Each cell is one hour of the last year. Blue is cold, red is warm."))



register(ResultView("hourly", "Hourly", 50, render, available=lambda ctx: ctx.result.hourly_temperatures is not None))
