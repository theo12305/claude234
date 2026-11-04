"""Calculations behind the result views, cached on the exact project JSON so going back to earlier inputs, switching
views or a second visitor with the same inputs is instant. ``from .cache import *`` gives a view all of them."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import analysis, model
from ..i18n import t

__all__ = ["cached_size", "cached_sensitivity", "cached_optimisation", "cached_load_optimisation",
           "cached_ground_map", "cached_uniform", "cached_borehole_map", "load_optimisation_done",
           "sensitivity_table", "layout_table"]


@st.cache_resource(max_entries=16, show_spinner=False)
def cached_size(project_json: str) -> model.SizingResult:
    """Sizing is cached on the exact inputs, so going back to earlier inputs is instant."""
    return model.size(model.from_json(project_json)[1])


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_sensitivity(project_json: str) -> pd.DataFrame:
    return analysis.sensitivity(model.from_json(project_json)[1])


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_optimisation(project_json: str, *limits) -> pd.DataFrame:
    return analysis.optimise_layout(model.from_json(project_json)[1], *limits)


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_load_optimisation(project_json: str, objective: str) -> dict | None:
    return analysis.load_optimisation(cached_size(project_json), objective)


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_ground_map(project_json: str) -> dict | None:
    return analysis.ground_temperature_map(cached_size(project_json))


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_uniform(project_json: str) -> tuple[float, float]:
    """The same design sized with one average conductivity and heat capacity instead of the layers."""
    return analysis.uniform_ground_length(cached_size(project_json), model.from_json(project_json)[1])


@st.cache_resource(max_entries=8, show_spinner=False)
def cached_borehole_map(project_json: str, years: float | None) -> pd.DataFrame:
    return analysis.borehole_map(cached_size(project_json), years)


def sensitivity_table(sens: pd.DataFrame) -> pd.DataFrame:
    table = sens.rename(columns={"Input": t("Input"), "Low": t("Input lower [m]"), "High": t("Input higher [m]"),
                                 "Base": t("Base [m]"), "Spread": t("Spread [m]")})
    table[t("Input")] = table[t("Input")].map(t)
    return table



def layout_table(table: pd.DataFrame) -> pd.DataFrame:
    table = table.copy()
    table["Layout"] = table["Layout"].map(t)
    return table.rename(columns=t)



def load_optimisation_done(sized_json: str) -> dict | None:
    """The load optimisation the user ran for this result, if any."""
    ran = st.session_state.get("load_opt")
    if ran and ran[0] == sized_json:
        return cached_load_optimisation(sized_json, ran[1])
    return None

