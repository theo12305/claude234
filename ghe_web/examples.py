"""Example projects for the start page: typical buildings with every input filled in, so a first-time user sees
a finished design in one click and can change it from there."""
from __future__ import annotations

from dataclasses import dataclass

from . import model, properties
from .properties import SectionInput


@dataclass(frozen=True)
class Example:
    key: str
    icon: str
    title: str
    description: str
    changes: dict  # section -> (variant, values on top of the variant's defaults)

    def inputs(self) -> dict[str, SectionInput]:
        inputs = model.default_inputs()
        for section, (variant, values) in self.changes.items():
            defaults = properties.get(section).variant(variant).defaults()
            inputs[section] = SectionInput(variant, {**defaults, **values})
        return inputs


def _l_shaped_field() -> tuple:
    """48 boreholes in an L along two sides of a schoolyard, 7 m apart."""
    long_side = [(x * 7.0, y * 7.0) for x in range(12) for y in range(3)]
    short_side = [(x * 7.0, 21.0 + y * 7.0) for x in range(3) for y in range(4)]
    return tuple(long_side + short_side)


EXAMPLES = (
    Example("house", "🏠", "Single-family house",
            "10 kW heat pump for heating and hot water, three boreholes in sandy clay.",
            {"ground": ("constant", {"k_s": 2.0, "T_g": 10.5, "volumetric_heat_capacity": 2.3}),
             "borefield": ("rectangular", {"N_1": 3, "N_2": 1, "B_1": 8.0, "B_2": 8.0, "H": 100.0}),
             "load": ("annual_building", {"annual_heating_mwh": 18.0, "peak_heating_kw": 10.0,
                                          "annual_cooling_mwh": 0.0, "peak_cooling_kw": 0.0, "scop": 4.5,
                                          "dhw_mwh": 3.0}),
             "limits": ("average_fluid", {"T_min": -1.5, "T_max": 17.0})}),
    Example("apartments", "🏢", "Apartment building",
            "24 flats, 60 kW heating and hot water, 25 boreholes in sandstone.",
            {"ground": ("constant", {"k_s": 2.6, "T_g": 10.0, "volumetric_heat_capacity": 2.2}),
             "borefield": ("rectangular", {"N_1": 5, "N_2": 5, "B_1": 7.0, "B_2": 7.0, "H": 100.0}),
             "load": ("annual_building", {"annual_heating_mwh": 110.0, "peak_heating_kw": 60.0,
                                          "annual_cooling_mwh": 0.0, "peak_cooling_kw": 0.0, "scop": 4.2,
                                          "dhw_mwh": 35.0}),
             "limits": ("average_fluid", {"T_min": -1.0, "T_max": 17.0})}),
    Example("office", "🏬", "Office with cooling",
            "400 MWh heating and 150 MWh cooling a year; cooling in summer puts heat back. 64 boreholes.",
            {"borefield": ("rectangular", {"N_1": 8, "N_2": 8, "B_1": 6.0, "B_2": 6.0, "H": 100.0}),
             "load": ("annual_building", {})}),
    Example("school", "🏫", "School",
            "Heating only, 48 boreholes in an L along the schoolyard, ground temperature rising with depth.",
            {"ground": ("gradient", {"k_s": 2.4, "T_g": 9.5, "gradient": 3.0, "volumetric_heat_capacity": 2.3}),
             "borefield": ("custom", {"points": _l_shaped_field(), "H": 120.0}),
             "load": ("annual_building", {"annual_heating_mwh": 260.0, "peak_heating_kw": 150.0,
                                          "annual_cooling_mwh": 0.0, "peak_cooling_kw": 0.0, "scop": 4.3,
                                          "dhw_mwh": 10.0})}),
)


def get(key: str) -> Example:
    return next(e for e in EXAMPLES if e.key == key)
