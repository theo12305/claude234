"""Further analysis: sensitivity, kept variants and the layout optimisation."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ... import analysis, export, i18n, model, plots, report, ui
from ...i18n import fmt, t
from ..cache import *  # noqa: F403 (the cached calculations)
from ..common import TEMPERATURE_CAPTION, figure, in_language, key_table
from ..registry import Ctx, ResultView, register


def render(ctx: Ctx) -> None:
    result, key, sized_json, sized_inputs = ctx.result, ctx.key, ctx.sized_json, ctx.sized_inputs
    with st.expander(t("Sensitivity check: what the borehole length depends on"), icon=":material/tune:"):
        ui.caption(t("Sizes the field again with one input changed at a time (monthly sizing for speed). The longest "
                     "bars are the inputs worth measuring carefully, e.g. with a thermal response test."))
        if st.button(t("Run the sensitivity check")):
            st.session_state.sensitivity_json = sized_json
        if st.session_state.get("sensitivity_json") == sized_json:
            with st.spinner(t("Sizing the variations...")):
                sens = cached_sensitivity(sized_json)
            figure(plots.tornado_chart(sens))
            base = float(sens["Base"].iloc[0])
            table = pd.DataFrame({t("Input"): sens["Input"].map(t),
                                  t("Length, input lower [m]"): sens["Low"],
                                  t("Length, input higher [m]"): sens["High"],
                                  t("Change, lower [%]"): (sens["Low"] / base - 1) * 100,
                                  t("Change, higher [%]"): (sens["High"] / base - 1) * 100})
            st.dataframe(table.round(1), hide_index=True)
            if result.sizing_method != "monthly":
                ui.caption(t("The variations use monthly sizing, which gives {base:.1f} m for these inputs (the "
                             "result above: {length:.1f} m). Read the changes in percent.", base=base,
                             length=result.borehole_length))

    with st.expander(t("Compare variants"), icon=":material/compare_arrows:"):
        ui.caption(t("Keep this result, change the inputs, size again and keep that one too. The comparison stays "
                     "until you close the page and is part of the Excel export."))
        label_col, button_col = st.columns([3, 1], vertical_alignment="bottom")
        variant_name = label_col.text_input(t("Name for this result"),
                                            value=t("Variant {n}", n=len(st.session_state.get("kept", [])) + 1))
        if button_col.button(t("Keep this result"), width="stretch", icon=":material/push_pin:"):
            row = {"Variant": variant_name, "Boreholes": result.number_of_boreholes,
                   "Length each [m]": round(result.borehole_length, 1), "Total length [m]": round(result.total_length),
                   "Lowest temp. [°C]": round(key.values["t_min"], 2),
                   "Highest temp. [°C]": round(key.values["t_max"], 2),
                   "Rb [m·K/W]": round(result.borehole_resistance, 3)}
            st.session_state.setdefault("kept", []).append(row)
        kept = st.session_state.get("kept", [])
        if kept:
            table = pd.DataFrame(kept)
            st.dataframe(table.rename(columns=t), hide_index=True, width="stretch")
            figure(plots.comparison_chart(table, "Total length [m]", t("Total length [m]")))
            if st.button(t("Clear the comparison")):
                st.session_state.kept = []
                st.rerun()

    with st.expander(t("Optimise the layout for a plot"), icon=":material/grid_view:"):
        ui.caption(t("Searches rectangular, L, U, box and staggered fields that fit in the plot and meet the "
                     "temperature limits, and lists the ones with the least drilling. Each trial takes a few "
                     "seconds."))
        with st.form("optimise"):
            o1, o2, o3 = st.columns(3)
            plot_l = o1.number_input(t("Plot length [m]"), 10.0, 1000.0, 70.0, 5.0)
            plot_w = o1.number_input(t("Plot width [m]"), 10.0, 1000.0, 70.0, 5.0)
            b_min = o2.number_input(t("Minimum spacing [m]"), 3.0, 20.0, 5.0, 0.5)
            b_max = o2.number_input(t("Maximum spacing [m]"), 3.0, 20.0, 8.0, 0.5)
            h_min = o3.number_input(t("Minimum borehole length [m]"), 20.0, 800.0, 50.0, 5.0)
            h_max = o3.number_input(t("Maximum borehole length [m]"), 20.0, 800.0, 150.0, 5.0)
            trials = st.slider(t("Number of trials (more finds better fields, but takes longer)"), 10, 100, 20, 5)
            go = st.form_submit_button(t("Find layouts"), icon=":material/search:")
        if go:
            with st.spinner(t("Trying {n} layouts. This takes about {minutes} minute(s)...", n=trials,
                              minutes=trials * 5 // 60 + 1)):
                try:
                    st.session_state.optimised = cached_optimisation(sized_json, plot_l, plot_w, b_min, b_max,
                                                                     h_min, h_max, trials)
                    st.session_state.optimised_json = sized_json
                except Exception as exc:
                    st.session_state.pop("optimised", None)
                    st.error(t("No layout found: {error}", error=exc))
        if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
            st.dataframe(layout_table(st.session_state.optimised.round(1)), hide_index=True, width="stretch")



def analysis_tables(ctx: Ctx) -> dict[str, pd.DataFrame]:
    """Analysis the user ran for this result, so the export contains it too."""
    sized_json, extra = ctx.sized_json, {}
    if st.session_state.get("sensitivity_json") == sized_json:
        extra[t("Sensitivity")] = sensitivity_table(cached_sensitivity(sized_json))
    if st.session_state.get("kept"):
        extra[t("Variant comparison")] = pd.DataFrame(st.session_state.kept).rename(columns=t)
    if st.session_state.get("optimised_json") == sized_json and "optimised" in st.session_state:
        extra[t("Layout optimisation")] = layout_table(st.session_state.optimised)
    return extra


# Drawn in its own step after the results (app.py), not on the results sheet
register(ResultView("analysis", "Further analysis", 900, render, tables=analysis_tables, on_sheet=False))
