"""The calculations behind the "Try it" exercises of the introduction, on a small practice project (6 boreholes
for a small office). No Streamlit here; the page caches the results.

Every number comes from the real sizing (``model.size``), so the exercises show what the app shows on a project.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from ..core import analysis, model
from ..inputs import registry as input_registry

LOAD_FACTOR = 0.13  # the example office load of the defaults, scaled down to a 6-borehole field


def practice_inputs() -> dict:
    """The practice project: 3 × 2 boreholes, 6 m apart, ground 2.0 W/(m·K), office load with summer cooling."""
    inputs = model.default_inputs()
    inputs["borefield"].values.update(N_1=3, N_2=2, B_1=6.0, B_2=6.0)
    inputs["ground"].values["k_s"] = 2.0
    variant = input_registry.get("load").variant(inputs["load"].variant)
    inputs["load"].values = analysis._scaled_load(inputs["load"].values, LOAD_FACTOR, variant)
    return inputs


def practice_json() -> str:
    return model.to_json(practice_inputs(), "Practice project")


def ks_sweep() -> pd.DataFrame:
    """Required length for ground conductivities from 1.0 to 4.0 W/(m·K)."""
    return analysis.sweep(practice_inputs(), "ground", "k_s", np.round(np.arange(1.0, 4.01, 0.25), 2))


def spacing_sweep() -> pd.DataFrame:
    """Required length for borehole spacings from 3 to 15 m."""
    return analysis.sweep(practice_inputs(), "borefield", "B_1", [3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 15.0])


def without_cooling(inputs: dict) -> dict:
    """The same project with the cooling removed (monthly loads only)."""
    out = copy.deepcopy(inputs)
    values = dict(out["load"].values)
    for k, v in values.items():
        if isinstance(v, (list, tuple)) and ("injection" in k or "cooling" in k):
            values[k] = type(v)(0.0 for _ in v)
    out["load"].values = values
    return out


def ground_years(years=(5, 25, 50)) -> dict:
    """The practice field with and without summer cooling, same length: the coldest fluid temperature per year and
    the ground map after the given years. Also the length the field would need without cooling."""
    with_c = practice_inputs()
    sized = model.size(with_c)
    no_c = without_cooling(with_c)
    no_c["borefield"].values["H"] = sized.borehole_length
    no_c["calculation"].variant = "check"
    checked = model.size(no_c)
    no_c_sized = without_cooling(practice_inputs())
    out = {"length": sized.borehole_length, "length_without": model.size(no_c_sized).borehole_length, "cases": {}}
    for case, result in (("cooling", sized), ("heating", checked)):
        out["cases"][case] = {"yearly": analysis.yearly_extremes(result),
                              "maps": {y: analysis.ground_temperature_map(result, cells=50, years=y) for y in years}}
    return out


def borehole_experiments() -> dict:
    """R_b and the required length for three grouts and three flow rates, and the R_b split of the practice field."""
    from . import explain
    base = practice_inputs()
    rows = {"grout": [], "flow": []}
    for kg in (0.8, 1.6, 2.4):
        trial = copy.deepcopy(base)
        trial["pipe"].values["k_g"] = kg
        r = model.size(trial)
        rows["grout"].append({"Value": kg, "Rb": r.borehole_resistance, "Length": r.borehole_length})
    for mfr in (0.15, 0.3, 0.6):
        trial = copy.deepcopy(base)
        trial["flow"].values["mfr"] = mfr
        r = model.size(trial)
        rows["flow"].append({"Value": mfr, "Rb": r.borehole_resistance, "Length": r.borehole_length,
                             "Re": r.reynolds})
    result = model.size(base)
    b = analysis.coldest_breakdown(result)
    return {"grout": pd.DataFrame(rows["grout"]), "flow": pd.DataFrame(rows["flow"]),
            "parts": explain.resistance_parts(result, b["fluid"] if b else 0.0),
            "Rb": result.borehole_resistance, "q_peak": b["q_peak"] if b else None,
            "fluid": b["fluid"] if b else None, "length": result.borehole_length}
