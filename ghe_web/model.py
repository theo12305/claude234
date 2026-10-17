"""Turns the user's inputs into a GHEtool Borefield and runs calculations.

This module has no web code, so it can be tested and reused on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from GHEtool import Borefield

from . import properties
from .properties import SectionInput
from .properties.pipe import ConstantRb


def default_inputs() -> dict[str, SectionInput]:
    """Each section with its first variant and default values."""
    return {s.key: SectionInput(s.variant().key, s.variant().defaults()) for s in properties.sections()}


def warnings(inputs: dict[str, SectionInput]) -> dict[str, list[str]]:
    """Soft warnings per section key: unusual but allowed inputs."""
    out = {}
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        if not variant.validate(chosen.values):
            msgs = variant.check_warnings(chosen.values)
            if msgs:
                out[section.key] = msgs
    return out


def validate(inputs: dict[str, SectionInput]) -> dict[str, list[str]]:
    """Return errors per section key. An empty dict means everything is valid."""
    errors = {}
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            errors[section.key] = [f"{section.label}: no input given."]
            continue
        problems = section.variant(chosen.variant).validate(chosen.values)
        if problems:
            errors[section.key] = problems
    if not errors:
        for key, msg in _cross_errors(inputs):
            errors.setdefault(key, []).append(msg)
    return errors


def _cross_errors(inputs: dict[str, SectionInput]) -> list[tuple[str, str]]:
    """Checks that need more than one section: the pipes have to fit in the borehole. GHEtool does not check
    this and returns a borehole resistance that is too low when they don't."""
    pipe, r_b = inputs["pipe"], inputs["borefield"].values.get("r_b_mm")
    v = pipe.values
    if r_b is None:
        return []
    if pipe.variant in ("single_u", "double_u"):
        if v["D_s_mm"] + v["r_out_mm"] > r_b:
            return [("pipe", f"The pipes stick out of the borehole: shank spacing + outer radius "
                             f"({v['D_s_mm'] + v['r_out_mm']:g} mm) is more than the borehole radius ({r_b:g} mm).")]
        # legs sit on a circle of radius D_s: two (single U) or four at 90° (double U)
        gap = 2 * v["D_s_mm"] if pipe.variant == "single_u" else 2 ** 0.5 * v["D_s_mm"]
        if gap < 2 * v["r_out_mm"]:
            return [("pipe", f"The pipe legs overlap: increase the shank spacing to at least "
                             f"{2 * v['r_out_mm'] / (2 if pipe.variant == 'single_u' else 2 ** 0.5):.1f} mm or "
                             "use smaller pipes.")]
    elif pipe.variant == "coaxial" and v["r_out_out_mm"] >= r_b:
        return [("pipe", f"The outer pipe ({v['r_out_out_mm']:g} mm radius) does not fit in the borehole "
                         f"({r_b:g} mm radius).")]
    return []


def _build(inputs: dict[str, SectionInput], key: str) -> Any:
    chosen = inputs[key]
    return properties.get(key).variant(chosen.variant).build(chosen.values)


def uses_building_load(inputs: dict[str, SectionInput]) -> bool:
    """True when the load is building demand, so a heat pump efficiency applies."""
    return inputs["load"].variant in ("annual_building", "hourly_building")


def temperature_dependent_cop(inputs: dict[str, SectionInput]) -> bool:
    return "heat_pump" in inputs and inputs["heat_pump"].variant == "curve" and uses_building_load(inputs)


def cross_warnings(inputs: dict[str, SectionInput]) -> dict[str, list[str]]:
    """Warnings that need more than one section."""
    out = {}
    if "heat_pump" in inputs and inputs["heat_pump"].variant == "curve" and not uses_building_load(inputs):
        out["heat_pump"] = ["The ground load is entered directly (monthly energy), so there is no heat pump to "
                            "apply this to. Choose yearly or hourly building demand in Ground load to use it."]
    return out


def _load(inputs: dict[str, SectionInput]):
    load = _build(inputs, "load")
    if temperature_dependent_cop(inputs):
        efficiency = _build(inputs, "heat_pump")
        load.cop = efficiency["cop"]
        load.eer = efficiency["eer"]
    return load


def build_borefield(inputs: dict[str, SectionInput]) -> Borefield:
    errors = validate(inputs)
    if errors:
        raise ValueError("; ".join(msg for msgs in errors.values() for msg in msgs))

    pipe = _build(inputs, "pipe")
    if isinstance(pipe, ConstantRb):
        borefield = Borefield(ground_data=_build(inputs, "ground"), load=_load(inputs))
        borefield.set_Rb(pipe.Rb)
        borefield.calculation_setup(use_constant_Rb=True)
    else:
        borefield = Borefield(
            ground_data=_build(inputs, "ground"),
            pipe_data=pipe,
            fluid_data=_build(inputs, "fluid"),
            flow_data=_build(inputs, "flow"),
            load=_load(inputs),
        )
    method, kwargs = _build(inputs, "borefield")
    getattr(borefield, method)(**kwargs)

    limits = _build(inputs, "limits")
    # GHEtool rejects a minimum above the current maximum (and vice versa), so order matters.
    if limits["T_min"] < borefield.Tf_max:
        borefield.set_min_fluid_temperature(limits["T_min"])
        borefield.set_max_fluid_temperature(limits["T_max"])
    else:
        borefield.set_max_fluid_temperature(limits["T_max"])
        borefield.set_min_fluid_temperature(limits["T_min"])
    return borefield


@dataclass
class SizingResult:
    borehole_length: float  # m per borehole
    number_of_boreholes: int
    total_length: float  # m
    borehole_resistance: float  # m·K/W
    borefield: Borefield
    temperatures: pd.DataFrame  # monthly fluid and borehole wall temperatures, index = years
    hourly_temperatures: pd.DataFrame | None = None  # only for hourly loads, index = hour of the simulation
    sizing_method: str = "monthly"  # "monthly", "hourly", or "check" when the length was given
    heat_pump: pd.DataFrame | None = None  # per year: electricity and seasonal performance (building loads only)
    hourly_basis: bool = False  # True when the limits were checked hour by hour (L4); the monthly table is then
    # only an approximation with block peaks, and the key results come from the hourly run
    reynolds: float | None = None  # at the lowest fluid temperature of the run the limits were checked with


def _optional(results, attr: str):
    """A result array that GHEtool may not have (it raises instead of returning an empty array)."""
    try:
        return getattr(results, attr)
    except (AttributeError, ValueError):
        return []


def temperature_table(borefield: Borefield) -> pd.DataFrame:
    """Monthly temperatures of the last calculation, one row per month, indexed by time in years."""
    r = borefield.results
    n = len(r.Tb)
    columns = {
        "Borehole wall": r.Tb,
        "Average fluid (base load)": r.baseload_temperature,
        "Average fluid (peak extraction)": r.peak_extraction,
        "Average fluid (peak injection)": r.peak_injection,
    }
    # supply and return temperatures exist when GHEtool knows the pipe and flow (not with a measured Rb)
    for label, attr in (("Into borefield (peak extraction)", "peak_extraction_inlet"),
                        ("Out of borefield (peak extraction)", "peak_extraction_outlet"),
                        ("Into borefield (peak injection)", "peak_injection_inlet"),
                        ("Out of borefield (peak injection)", "peak_injection_outlet")):
        values = _optional(r, attr)
        if len(values) == n:
            columns[label] = values
    return pd.DataFrame(columns, index=pd.Index([(i + 1) / 12 for i in range(n)], name="Years"))


def hourly_temperature_table(borefield: Borefield) -> pd.DataFrame:
    """Hourly temperatures of the last hourly calculation, indexed by hour of the simulation."""
    r = borefield.results
    columns = {"Borehole wall": r.Tb, "Average fluid": r.Tf}
    inlet, outlet = _optional(r, "peak_extraction_inlet"), _optional(r, "peak_extraction_outlet")
    if len(inlet) == len(r.Tf):  # hourly results have one inlet/outlet series (not per peak)
        columns["Into borefield"], columns["Out of borefield"] = inlet, outlet
    return pd.DataFrame(columns, index=pd.RangeIndex(1, len(r.Tf) + 1, name="Hour"))


def size(inputs: dict[str, SectionInput]) -> SizingResult:
    borefield = build_borefield(inputs)
    load_values = inputs["load"].values
    is_hourly = getattr(borefield.load, "_hourly", False)
    hourly_sizing = is_hourly and load_values.get("hourly_sizing", False)
    check_only = inputs.get("calculation") is not None and inputs["calculation"].variant == "check"
    if check_only:
        length = borefield.H
    else:
        length = borefield.size(L4_sizing=True) if hourly_sizing else borefield.size()
    n = borefield.number_of_boreholes

    hourly_temps = heat_pump = reynolds = None
    if is_hourly:
        borefield.calculate_temperatures(length, hourly=True)
        hourly_temps = hourly_temperature_table(borefield)
        if hourly_sizing:  # electricity and Re from the same (hourly) temperatures the sizing used
            heat_pump = heat_pump_table(borefield.load)
            reynolds = _reynolds(borefield)
    borefield.calculate_temperatures(length)
    if heat_pump is None:
        heat_pump = heat_pump_table(borefield.load)
    if reynolds is None:
        reynolds = _reynolds(borefield)
    return SizingResult(length, n, length * n, borefield.Rb, borefield, temperature_table(borefield),
                        hourly_temps, "check" if check_only else "hourly" if hourly_sizing else "monthly", heat_pump,
                        hourly_basis=bool(hourly_sizing), reynolds=reynolds)


def _reynolds(borefield: Borefield) -> float | None:
    if borefield.borehole.use_constant_Rb:
        return None
    try:
        return float(borefield.Re)  # GHEtool evaluates it at the lowest fluid temperature, the worst case
    except Exception:
        return None


def heat_pump_table(load) -> pd.DataFrame | None:
    """Electricity use and seasonal performance per simulated year, for building loads. With a temperature-
    dependent COP these change over the years as the ground temperature changes."""
    if not hasattr(load, "yearly_electricity_consumption_heating"):
        return None
    years = load.simulation_period

    def yearly(monthly):
        return np.asarray(monthly, dtype=float).reshape(years, 12).sum(axis=1)

    heating = yearly(load._monthly_baseload_heating_simulation_period_with_limit)
    cooling = yearly(load._monthly_baseload_cooling_simulation_period_with_limit)
    dhw = yearly(load._monthly_baseload_dhw_simulation_period_with_limit)
    e_heat = np.asarray(load.yearly_electricity_consumption_heating, dtype=float)
    e_cool = np.asarray(load.yearly_electricity_consumption_cooling, dtype=float)
    e_dhw = np.asarray(load.yearly_electricity_consumption_dhw, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return pd.DataFrame({
            "Year": np.arange(1, years + 1),
            "Heating demand [MWh]": heating / 1000, "Cooling demand [MWh]": cooling / 1000,
            "Hot water demand [MWh]": dhw / 1000,
            "Electricity heating [MWh]": e_heat / 1000, "Electricity cooling [MWh]": e_cool / 1000,
            "Electricity hot water [MWh]": e_dhw / 1000,
            "SPF heating": np.where(e_heat > 0, heating / e_heat, np.nan),
            "SEER": np.where(e_cool > 0, cooling / e_cool, np.nan),
        })


# ---------------------------------------------------------------- saving and loading

PROJECT_FORMAT = 1


def to_json(inputs: dict[str, SectionInput], name: str = "") -> str:
    import json
    return json.dumps({
        "format": PROJECT_FORMAT,
        "name": name,
        "sections": {k: {"variant": v.variant, "values": _plain(v.values)} for k, v in inputs.items()},
    }, indent=2)


def from_json(text: str) -> tuple[str, dict[str, SectionInput]]:
    """Read a saved project. Sections, variants or values that no longer exist are dropped and
    missing ones get their defaults, so files stay loadable when the interface is extended."""
    import json
    data = json.loads(text)
    if data.get("format") != PROJECT_FORMAT:
        raise ValueError("This file is not a GHEtool Web project.")
    inputs = default_inputs()
    for key, saved in data.get("sections", {}).items():
        try:
            variant = properties.get(key).variant(saved.get("variant"))
        except KeyError:
            continue
        values = variant.defaults()
        for p in variant.properties:
            if p.key in saved.get("values", {}):
                v = saved["values"][p.key]
                if p.kind == "monthly":
                    v = tuple(v)
                elif p.kind == "points":
                    v = tuple(tuple(pt) for pt in v)
                values[p.key] = v
        inputs[key] = SectionInput(variant.key, values)
    return data.get("name", ""), inputs


def _plain(values: dict[str, Any]) -> dict[str, Any]:
    def plain(v):
        return [plain(x) for x in v] if isinstance(v, (list, tuple)) else v
    return {k: plain(v) for k, v in values.items()}
