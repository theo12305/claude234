"""Layers: the ground layers along the borehole (only with a layer table)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, sized_inputs, sized_json = ctx.result, ctx.sized_inputs, ctx.sized_json
    from ghe_web.strata import predict
    rows, used = plots.ground_rows(sized_inputs)
    length, buried = result.borehole_length, sized_inputs["borefield"].values["D"]
    k, c = predict.effective(rows, length, buried)
    parts = predict.contributions(rows, length, buried)
    if not used:
        st.info(t("These layers were not used: the calculation took the single conductivity from step ①. Switch on "
                  "**Calculate with the layers** under Ground to size with them."), icon=":material/info:")
    c1, c2, c3 = st.columns(3)
    c1.metric(t("Average conductivity along the borehole"), fmt("{x:.2f} W/(m·K)", x=k),
              t("from {top:.1f} to {bottom:.0f} m", top=buried, bottom=buried + length), delta_color="off",
              delta_arrow="off")
    c2.metric(t("Average heat capacity"), fmt("{x:.2f} MJ/(m³·K)", x=c))
    c3.metric(t("Layers reached"), t("{n} of {total}", n=len(parts), total=len(rows)))
    left, right = st.columns([2, 3], gap="large")
    with left:
        st.pyplot(plots.borehole_log(rows, length, buried, t("{n} boreholes of {length:.1f} m",
                                                             n=result.number_of_boreholes, length=length)),
                  width="stretch")
    with right:
        st.markdown(t("**Share of the heat exchange per layer**"))
        figure(plots.layer_share_chart(parts))
        ui.caption(t("Length in the layer × its conductivity, as a share of the whole borehole. Layers that conduct "
                     "well carry more of the heat, so they are worth reaching."))
        st.markdown(t("**Average conductivity for other borehole lengths**"))
        top = max(float(rows[-1]["top"]) * 1.2, length * 1.6, 50.0)
        figure(plots.conductivity_with_length(rows, buried, range(10, int(top) + 1, 5), length))
        ui.caption(t("Dashed: the calculated length. Where the curve rises, a deeper borehole reaches better "
                     "ground."))
    if used:
        with st.expander(t("Compare: the same design with one average value"), icon=":material/compare_arrows:"):
            ui.caption(t("Sizes again with a single conductivity and heat capacity, the average over the borehole "
                         "length found here. The difference shows how much the layering matters."))
            if st.button(t("Calculate the comparison"), key="uniform_go"):
                st.session_state.uniform_json = sized_json
            if st.session_state.get("uniform_json") == sized_json:
                with st.spinner(t("Sizing with the average values...")):
                    try:
                        uniform, k_used = cached_uniform(sized_json)
                    except Exception as exc:
                        st.error(t("The comparison failed: {error}", error=exc))
                        return
                d1, d2 = st.columns(2)
                d1.metric(t("With layers"), fmt("{x:.1f} m", x=length))
                d2.metric(t("With one value ({k:.2f} W/(m·K))", k=k_used), fmt("{x:.1f} m", x=uniform),
                          t("{x:+.1f} m per borehole", x=uniform - length), delta_color="off", delta_arrow="off")



register(ResultView("layers", "Layers", 100, render,
                    available=lambda ctx: bool((ctx.sized_inputs["ground"].values.get("layers") or {}).get("rows"))))
