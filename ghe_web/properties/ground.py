from GHEtool import GroundConstantTemperature, GroundFluxTemperature

from .base import Property, Section, Variant
from .registry import register

K_S = Property("k_s", "Ground thermal conductivity", 3.0, "W/(m·K)", min=0.1, max=10.0, step=0.1)
T_G = Property("T_g", "Undisturbed ground temperature", 10.0, "°C", min=-10.0, max=40.0, step=0.5)
C_VOL = Property("volumetric_heat_capacity", "Volumetric heat capacity", 2.4, "MJ/(m³·K)",
                 min=0.5, max=5.0, step=0.1)

register(Section(
    key="ground",
    label="Ground",
    order=10,
    variants=(
        Variant(
            key="constant",
            label="Constant ground temperature",
            properties=(K_S, T_G, C_VOL),
            build=lambda v: GroundConstantTemperature(
                k_s=v["k_s"], T_g=v["T_g"], volumetric_heat_capacity=v["volumetric_heat_capacity"] * 1e6),
        ),
        Variant(
            key="flux",
            label="Surface temperature with geothermal heat flux",
            help="Ground temperature rises with depth because of the geothermal heat flux.",
            properties=(K_S, T_G, C_VOL,
                        Property("flux", "Geothermal heat flux", 0.06, "W/m²", min=0.0, max=0.5, step=0.01)),
            build=lambda v: GroundFluxTemperature(
                k_s=v["k_s"], T_g=v["T_g"], volumetric_heat_capacity=v["volumetric_heat_capacity"] * 1e6,
                flux=v["flux"]),
        ),
    ),
))
