"""Borefield map: the load share and temperature change of each borehole."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


FIELD_COLOURS = {"share": "Share of the load", "change": "Temperature change"}


def render(ctx: Ctx) -> None:
    result, sized_json, name = ctx.result, ctx.sized_json, ctx.name
    years = result.borefield.load.simulation_period
    c1, c2 = st.columns(2)
    colour = c1.selectbox(t("Colour by"), list(FIELD_COLOURS), format_func=lambda k: t(FIELD_COLOURS[k]),
                          index=list(FIELD_COLOURS).index("share"), key="field_colour")
    when = c2.selectbox(t("Time"), ["first", "last"], index=1, key="field_time",
                        format_func=lambda k: t("after 1 year") if k == "first" else t("after {n} years", n=years))
    with st.spinner(t("Calculating each borehole...")):
        table = cached_borehole_map(sized_json, 1.0 if when == "first" else None)
    if len(table) < 2:
        st.info(t("With a single borehole there is nothing to compare."), icon=":material/info:")
        return
    hi, lo = table.loc[table["Share"].idxmax()], table.loc[table["Share"].idxmin()]
    m1, m2, m3 = st.columns(3)
    m1.metric(t("Hardest-working borehole"), t("No. {n}", n=int(hi["Borehole"])),
              t("{x:.0f} % of the average load", x=hi["Share"] * 100), delta_color="off", delta_arrow="off")
    m2.metric(t("Least-loaded borehole"), t("No. {n}", n=int(lo["Borehole"])),
              t("{x:.0f} % of the average load", x=lo["Share"] * 100), delta_color="off", delta_arrow="off")
    m3.metric(t("Wall temperature change"), fmt("{a:+.1f} to {b:+.1f} K", a=table["Change"].min(),
                                                b=table["Change"].max()),
              t("from the yearly imbalance"), delta_color="off", delta_arrow="off")
    left, right = st.columns([3, 2])
    with left:
        figure(plots.borehole_map_chart(table, colour))
    with right:
        if colour == "share":
            ui.caption(t("GHEtool sizes the field with one wall temperature for all boreholes. To reach it, boreholes "
                         "at the edge and in the corners take more heat than those in the middle, because they have "
                         "fewer neighbours. Red: more than the average, blue: less. The difference grows over the "
                         "years as the boreholes start to influence each other."))
        else:
            ui.caption(t("How much the yearly imbalance warms (red) or cools (blue) the ground at each borehole wall, "
                         "with the same heat from every borehole. Boreholes in the middle change most, because their "
                         "neighbours add up; a larger spacing there, or moving boreholes to the edge, helps."))
        ui.caption(t("Finite line source with the mirror image at the surface, one segment per borehole (the same "
                     "model as the g-function). Numbers as in the input table of the borefield."))
        st.download_button(t("Download the table (CSV)"),
                           lambda: table.round(4).to_csv(index=False).encode(),
                           f"{name.strip() or 'ghetool-project'}_boreholes.csv", "text/csv",
                           icon=":material/download:", on_click="ignore")



register(ResultView("field", "Borefield map", 90, render))
