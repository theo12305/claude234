"""Temperatures: over the years, the last year, yearly extremes and the table."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


TEMP_VIEWS = {"years": "Over the years", "last": "Last year", "extremes": "Yearly min/max", "table": "Table"}


def render(ctx: Ctx) -> None:
    result, limits = ctx.result, ctx.limits
    if result.hourly_basis:
        st.info(t("These are the monthly temperatures with block peaks, shown for comparison. The sizing checked "
                  "the limits hour by hour: see **Hourly** for those temperatures."), icon=":material/info:")
    choice = st.selectbox(t("Chart"), list(TEMP_VIEWS), format_func=lambda k: t(TEMP_VIEWS[k]), key="temp_view_id")
    table = export.monthly_temperatures(result).round(3)
    if choice == "years":
        years = round(float(result.temperatures.index.max()))
        period = None
        if years > 1:
            period = st.slider(t("Years shown"), 0, years, (0, years), key="temp_period",
                               help=t("Zoom in on a part of the simulation period."))
            if tuple(period) == (0, years):
                period = None
        left, right = st.columns([3, 1], gap="medium")
        with left:
            figure(plots.temperature_chart(result.temperatures, limits, period), TEMPERATURE_CAPTION(), table)
        with right:
            figure(plots.last_year_chart(result.temperatures, limits, compact=True),
                   t("The last year enlarged: blue, grey and red as on the left."), table.tail(12))
    elif choice == "last":
        caption = t("Into the borefield = supply from the heat pump; out of the borefield = return to the heat pump.") \
            if "Into borefield (peak extraction)" in result.temperatures else None
        figure(plots.last_year_chart(result.temperatures, limits), caption, table.tail(12))
    elif choice == "extremes":
        extremes = analysis.yearly_extremes(result)
        figure(plots.yearly_extremes_chart(extremes, limits),
               t("If the lowest temperature keeps falling (or the highest keeps rising) every year, the ground is out "
                 "of balance. A longer simulation period shows whether it levels off."), extremes.round(3))
    else:
        st.dataframe(export.monthly_temperatures(result).round(2), hide_index=True, width="stretch", height=420)



register(ResultView("temperatures", "Temperatures", 30, render))
