"""Turns the user's inputs into a GHEtool Borefield and runs calculations.

This module has no web code, so it can be tested and reused on its own.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    return errors


def _build(inputs: dict[str, SectionInput], key: str) -> Any:
    chosen = inputs[key]
    return properties.get(key).variant(chosen.variant).build(chosen.values)


def build_borefield(inputs: dict[str, SectionInput]) -> Borefield:
    errors = validate(inputs)
    if errors:
        raise ValueError("; ".join(msg for msgs in errors.values() for msg in msgs))

    pipe = _build(inputs, "pipe")
    if isinstance(pipe, ConstantRb):
        borefield = Borefield(ground_data=_build(inputs, "ground"), load=_build(inputs, "load"))
        borefield.set_Rb(pipe.Rb)
        borefield.calculation_setup(use_constant_Rb=True)
    else:
        borefield = Borefield(
            ground_data=_build(inputs, "ground"),
            pipe_data=pipe,
            fluid_data=_build(inputs, "fluid"),
            flow_data=_build(inputs, "flow"),
            load=_build(inputs, "load"),
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
    return pd.DataFrame({"Borehole wall": r.Tb, "Average fluid": r.Tf},
                        index=pd.RangeIndex(1, len(r.Tf) + 1, name="Hour"))


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

    hourly_temps = None
    if is_hourly:
        borefield.calculate_temperatures(length, hourly=True)
        hourly_temps = hourly_temperature_table(borefield)
    borefield.calculate_temperatures(length)
    return SizingResult(length, n, length * n, borefield.Rb, borefield, temperature_table(borefield),
                        hourly_temps, "check" if check_only else "hourly" if hourly_sizing else "monthly")


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
