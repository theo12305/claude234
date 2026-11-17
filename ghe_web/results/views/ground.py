"""Ground: the temperature change around the field and the g-function."""
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
    result, sized_json = ctx.result, ctx.sized_json
    north = ctx.sized_inputs["borefield"].variant == "custom"
    with st.spinner(t("Calculating the ground temperature around the field...")):
        m = cached_ground_map(sized_json)
    if sheet.on("ground_numbers"):
        _numbers(m)
    if sheet.on("ground_map"):
        end = int(round(m["years"]))
        choices = sorted({y for y in (1, 2, 5, 10, 20, 25, 30, 40, 50, 75, 100) if y < end} | {end})
        year = st.select_slider(t("Year"), options=choices, value=end, key="ground_map_year",
                                help=t("Move through the years to see the ground change. The colours stay the same "
                                       "for every year, so the maps compare."))
        shown = m if year == end else {**cached_ground_map(sized_json, year),
                                       "scale": (float(m["table"]["Change"].min()), float(m["table"]["Change"].max()))}
        _map(shown, north)
    if sheet.on("gfunction"):
        ui.caption(t("The dimensionless step response of the field. Its rise at large times shows how strongly the "
                     "boreholes influence each other."))
        curve = analysis.gfunction_curve(result)
        figure(plots.gfunction_chart(curve), data=curve)


def _numbers(m: dict) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Undisturbed ground"), fmt("{x:.1f} °C", x=m["t_ground"]))
    c2.metric(t("Net heat flow into the ground"), fmt("{x:+.2f} W/m", x=m["q_w_per_m"]),
              t("yearly average per metre of borehole"), delta_color="off", delta_arrow="off")
    c3.metric(t("Largest change"), fmt("{x:.1f} K", x=m["max_change"]), t("after {n} years", n=m["years"]),
              delta_color="off", delta_arrow="off")


def _map(m: dict, north: bool) -> None:
    left, right = st.columns([11, 9], gap="medium")
    with left:
        figure(plots.ground_map_chart(m, north, size=290 if ui.is_phone() else 420), data=m["table"].round(4),
               width="content")
    with right:
        ui.caption(t("How the yearly imbalance warms (red) or cools (blue) the ground around the field after {n} "
                     "years, halfway down the boreholes. Lines: equal change, every {step:g} K. Each dot is a "
                     "borehole. Boreholes in the middle change most because their neighbours add up. The seasonal "
                     "swing on top of this averages out over a year and is left out.",
                     n=round(m["years"]), step=plots.ground_classes(m["table"]["Change"])[0]))
        ui.caption(t("Calculated with the finite line source (uniform heat flow per metre, with the mirror image at "
                     "the surface), which is also the basis of the g-function."))


register(ResultView("ground", "Ground", 80, render))
