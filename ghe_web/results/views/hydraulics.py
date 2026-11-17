"""Hydraulics: Rb, Reynolds number, pressure drop and pump power."""
from __future__ import annotations

import streamlit as st

from ghe_web.core import analysis
from ghe_web.page import look
from ghe_web.charts import result_charts
from ghe_web.i18n import fmt, t
from ghe_web.results.common import figure
from ghe_web.results.registry import Ctx, ResultView, hidden, register


def render(ctx: Ctx) -> None:
    result, key = ctx.result, ctx.key
    if result.reynolds is None:
        st.info(t("With a measured borehole resistance (TRT) the pipe and flow are not known, so there are no "
                  "hydraulic results."), icon=":material/info:")
        return
    v = key.values
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("Borehole thermal resistance Rb"), fmt("{x:.3f} m·K/W", x=result.borehole_resistance))
    c2.metric(t("Reynolds number"), fmt("{x:,.0f}", x=v["Re"]), analysis.regime(v["Re"]), delta_color="off",
              delta_arrow="off")
    if "dp_kpa" in v:
        c3.metric(t("Pressure drop per borehole"), fmt("{x:.1f} kPa", x=v["dp_kpa"]))
        c4.metric(t("Pump power"), fmt("{x:,.0f} W", x=v["pump_electric_w"]),
                  t("{x:,.1f} MWh per year", x=v["pump_mwh"]), delta_color="off", delta_arrow="off")
        curve = analysis.pressure_drop_curve(result, v["t_min"])
        if curve is not None:
            bf = result.borefield
            flow = float(bf.borehole.flow_data.vfr_borehole(fluid_data=bf.borehole.fluid_data,
                                                             temperature=v["t_min"]))
            figure(result_charts.pressure_drop_chart(curve, flow, v["dp_kpa"]))
            look.caption(t("At the coldest fluid temperature, where the fluid is most viscous. The borehole only: add "
                         "the manifold, header pipes and heat pump evaporator for the pump. The kink is where the "
                         "flow turns turbulent."))
    look.caption(t("Pump energy = hydraulic power ÷ pump efficiency × operating hours, both set under Flow rate in "
                 "step ②."))



register(ResultView("hydraulics", "Hydraulics", 70, render, available=hidden))  # not shown for now
