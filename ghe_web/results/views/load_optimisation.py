"""Load optimisation: how much of the hourly building demand the field can take."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, sized_json, name = ctx.result, ctx.sized_json, ctx.name
    ui.caption(t("Keeps the borefield as designed and works out how much of the hourly building demand it can take "
                 "within the temperature limits. The rest comes from a backup boiler, gas or electric, or a chiller "
                 "(a hybrid system). This answers: how far does a smaller or cheaper field get me?"))
    names = analysis.OBJECTIVES
    with st.form("load_opt_form"):
        notes_ = [t("the largest share of the peak power"), t("the most energy, month by month"),
                  t("the most power with no long-term imbalance (slow, 2 to 3 minutes)")]
        objective = st.selectbox(t("Optimise for"), list(names), format_func=lambda k: t(names[k]),
                                 help="  \n".join(f"**{t(names[k])}**: {n}" for k, n in zip(names, notes_)))
        go = st.form_submit_button(t("Optimise the load"), icon=":material/tune:", type="primary")
    if go:
        with st.spinner(t("Optimising the load split...")):
            try:
                cached_load_optimisation(sized_json, objective)
                st.session_state.load_opt = (sized_json, objective)
            except Exception as exc:
                st.error(t("The optimisation failed: {error}", error=exc))
    opt = load_optimisation_done(sized_json)
    if opt is None:
        return
    st.markdown(t("**Result: {objective}**", objective=t(names[opt["objective"]])))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Heating covered by the ground"), fmt("{x:.1%}", x=opt["heating_share"]))
    k2.metric(t("Cooling covered by the ground"), fmt("{x:.1%}", x=opt["cooling_share"]))
    k3.metric(t("Backup heating"), fmt("{x:,.0f} kW", x=opt["backup_heating_kw"]),
              t("{x:,.1f} MWh per year", x=opt["backup_heating_mwh"]), delta_color="off", delta_arrow="off")
    k4.metric(t("Backup cooling"), fmt("{x:,.0f} kW", x=opt["backup_cooling_kw"]),
              t("{x:,.1f} MWh per year", x=opt["backup_cooling_mwh"]), delta_color="off", delta_arrow="off")
    figure(plots.optimisation_chart(opt["monthly"]))
    ui.caption(t("Peak power taken by the ground: heating {heat:,.0f} kW, cooling {cool:,.0f} kW (building side).",
                 heat=opt["ground_peak_heating_kw"], cool=opt["ground_peak_cooling_kw"]))
    stem = name.strip() or "ghetool-project"
    st.download_button(t("Download the optimised load, first year hourly (CSV)"),
                       lambda: opt["first_year"].round(3).to_csv().encode(), f"{stem}_optimised_load.csv",
                       "text/csv", icon=":material/download:", on_click="ignore")



def load_optimisation_tables(ctx: Ctx) -> dict[str, pd.DataFrame]:
    opt = load_optimisation_done(ctx.sized_json)
    if opt is None:
        return {}
    monthly = opt["monthly"].round(3)
    monthly["Month"] = list(i18n.months())
    return {t("Load optimisation, monthly"): monthly.rename(columns=t),
            t("Load optimisation, yearly"): opt["yearly"].round(3).rename(columns=t)}


register(ResultView("load_optimisation", "Load optimisation", 110, render, tables=load_optimisation_tables,
                    available=lambda ctx: ctx.sized_inputs["load"].variant == "hourly_building"))
