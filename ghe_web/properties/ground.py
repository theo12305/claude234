from GHEtool import GroundConstantTemperature, GroundFluxTemperature, GroundTemperatureGradient

from ..catalog import GROUND
from .base import PresetGroup, Property, Section, Variant
from .registry import register

K_S = Property("k_s", "Ground thermal conductivity", 3.0, "W/(m·K)", min=0.1, max=10.0, step=0.1)
T_G = Property("T_g", "Undisturbed ground temperature", 10.0, "°C", min=-10.0, max=40.0, step=0.5)
T_SURFACE = Property("T_g", "Ground surface temperature", 10.0, "°C", min=-10.0, max=40.0, step=0.5,
                     help="Average yearly temperature at the surface; it increases with depth.")
C_VOL = Property("volumetric_heat_capacity", "Volumetric heat capacity", 2.4, "MJ/(m³·K)",
                 min=0.5, max=5.0, step=0.1)
ROCK = (PresetGroup("Rock type", GROUND, help="Typical values (VDI 4640). Use measured values if you have them."),)


def _conductivity_warning(v):
    if v["k_s"] > 4.5:
        return f"A ground conductivity of {v['k_s']} W/(m·K) is unusually high. Is it from a thermal response test?"
    if v["k_s"] < 1.0:
        return "Ground conductivity below 1 W/(m·K) is typical for dry soil only; boreholes will be long."


def _c(v):
    return v["volumetric_heat_capacity"] * 1e6


register(Section(
    key="ground",
    label="Ground",
    order=10,
    variants=(
        Variant(
            key="constant",
            label="Constant ground temperature",
            properties=(K_S, T_G, C_VOL),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: GroundConstantTemperature(k_s=v["k_s"], T_g=v["T_g"], volumetric_heat_capacity=_c(v)),
        ),
        Variant(
            key="flux",
            label="Surface temperature + heat flux",
            help="Ground temperature rises with depth because of the geothermal heat flux (as in EED).",
            properties=(K_S, T_SURFACE, C_VOL,
                        Property("flux", "Geothermal heat flux", 0.06, "W/m²", min=0.0, max=0.5, step=0.01)),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: GroundFluxTemperature(k_s=v["k_s"], T_g=v["T_g"], volumetric_heat_capacity=_c(v),
                                                  flux=v["flux"]),
        ),
        Variant(
            key="gradient",
            label="Surface temperature + gradient",
            help="Ground temperature rises linearly with depth. Recommended for boreholes deeper than about 150 m.",
            properties=(K_S, T_SURFACE, C_VOL,
                        Property("gradient", "Geothermal gradient", 3.0, "K/100 m", min=0.0, max=10.0, step=0.1)),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: GroundTemperatureGradient(k_s=v["k_s"], T_g=v["T_g"], volumetric_heat_capacity=_c(v),
                                                      gradient=v["gradient"]),
        ),
    ),
))
