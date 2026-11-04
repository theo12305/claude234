"""Heat pump: SPF, SEER, electricity and the efficiency curves (building loads only)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, key, sized_inputs = ctx.result, ctx.key, ctx.sized_inputs
    curve = sized_inputs["heat_pump"].variant == "curve"
    c1, c2, c3 = st.columns(3)
    if "spf_heating" in key.values:
        c1.metric(t("SPF heating"), fmt("{x:.2f}", x=key.values["spf_heating"]),
                  t("{x:+.2f} from year 1 to the last year", x=key.values["spf_last"] - key.values["spf_first"])
                  if curve else None, delta_color="off", delta_arrow="off")
    if "seer" in key.values:
        c2.metric(t("SEER cooling"), fmt("{x:.1f}", x=key.values["seer"]))
    c3.metric(t("Electricity per year"), fmt("{x:,.1f} MWh", x=key.values["electricity_mwh"]))
    if curve:
        lo = float(min(result.temperatures["Average fluid (peak extraction)"].min(), key.values["t_min"]))
        hi = float(max(result.temperatures["Average fluid (peak injection)"].max(), key.values["t_max"]))
        for c in plots.efficiency_curves(sized_inputs["heat_pump"].values, (lo, hi)):
            figure(c)
    else:
        st.info(t("The heat pump efficiency is fixed (SCOP/SEER). Choose **Depends on the fluid temperature** under "
                  "Heat pump efficiency in step ③ to see how the COP changes as the ground cools."),
                icon=":material/info:")
    charts = plots.heat_pump_yearly_chart(result.heat_pump, show_spf=curve)
    for c in charts if isinstance(charts, tuple) else (charts,):
        figure(c)



register(ResultView("heat_pump", "Heat pump", 60, render, available=lambda ctx: ctx.result.heat_pump is not None))
