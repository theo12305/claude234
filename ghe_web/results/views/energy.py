"""Energy: the monthly energy balance of the ground and the load duration curve."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from .. import sheet
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, key = ctx.result, ctx.key
    energy = analysis.monthly_ground_energy(result)
    years = round(float(result.temperatures.index.max()))
    drift = key.values.get("drift_k")
    net = float(energy["Injection"].sum() - energy["Extraction"].sum())
    text = t("Each year {x:,.0f} MWh more is taken from the ground than returned, so the ground slowly cools down.",
             x=-net) if net < 0 else t("Each year {x:,.0f} MWh more is returned to the ground than taken, so the "
                                       "ground slowly warms up.", x=net)
    if drift is not None:
        text += " " + t("The lowest fluid temperature changes by {x:+.1f} K from year 1 to year {n}.", x=drift, n=years)
    if sheet.on("energy_balance"):
        figure(plots.energy_balance_chart(energy),
               t("Blue, below zero: heat taken from the ground for heating; it cools the ground. Red, above zero: heat "
                 "put into the ground by cooling; it warms it. Grey line: what is left each month. Energy in the "
                 "ground, after the heat pump efficiency.") + " " + text, energy.round(3))
    if sheet.on("energy_numbers"):
        c1, c2, c3 = st.columns(3)
        c1.metric(t("Extracted from the ground"), t("{x:,.0f} MWh/yr", x=key.values["extraction_mwh"]))
        c2.metric(t("Injected into the ground"), t("{x:,.0f} MWh/yr", x=key.values["injection_mwh"]))
        c3.metric(t("Imbalance"), t("{x:+,.0f} MWh/yr", x=key.values["imbalance_mwh"]))
    duration = analysis.load_duration(result) if sheet.on("load_duration") else None
    if duration is not None:
        figure(plots.load_duration_chart(duration),
               t("Each load sorted from its highest hour to its lowest. Solid: building demand. Dashed: what the "
                 "ground sees after the heat pump. The area under a curve is the energy per year."), duration)



register(ResultView("energy", "Energy", 40, render))
