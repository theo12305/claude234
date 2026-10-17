from GHEtool import GroundConstantTemperature, GroundFluxTemperature, GroundLayer, GroundTemperatureGradient

from ..catalog import GROUND
from .base import PresetGroup, Property, Section, Variant
from .registry import register

K_S = Property("k_s", "Ground thermal conductivity", 3.0, "W/(m·K)", min=0.1, max=10.0, step=0.1)
T_G = Property("T_g", "Undisturbed ground temperature", 10.0, "°C", min=-10.0, max=40.0, step=0.5)
T_SURFACE = Property("T_g", "Ground surface temperature", 10.0, "°C", min=-10.0, max=40.0, step=0.5,
                     help="Average yearly temperature at the surface; it increases with depth.")
C_VOL = Property("volumetric_heat_capacity", "Volumetric heat capacity", 2.4, "MJ/(m³·K)",
                 min=0.5, max=5.0, step=0.1)
LAYERS = Property("layers", "Ground layers", {"use": False, "rows": ()}, kind="layers",
                  help="Layers from the surface down, each with its own conductivity and heat capacity. Predicted "
                       "from nearby borehole logs or entered by hand.")
ROCK = (PresetGroup("Rock type", GROUND, help="Typical values (VDI 4640). Use measured values if you have them."),)


def _conductivity_warning(v):
    if layered(v):
        return None
    if v["k_s"] > 4.5:
        return f"A ground conductivity of {v['k_s']} W/(m·K) is unusually high. Is it from a thermal response test?"
    if v["k_s"] < 1.0:
        return "Ground conductivity below 1 W/(m·K) is typical for dry soil only; boreholes will be long."


def _c(v):
    return v["volumetric_heat_capacity"] * 1e6


def layered(v) -> bool:
    """True when the calculation uses the layer table instead of the single conductivity."""
    layers = v.get("layers") or {}
    return bool(layers.get("use") and layers.get("rows"))


def _ground(cls, v, **kwargs):
    """A GHEtool ground with either one conductivity or the layers. GHEtool then averages the layers over the
    borehole length while it sizes, so a longer borehole reaches deeper layers."""
    if not layered(v):
        return cls(k_s=v["k_s"], volumetric_heat_capacity=_c(v), **kwargs)
    ground = cls(k_s=None, **kwargs)
    rows = v["layers"]["rows"]
    for i, r in enumerate(rows):
        last = i == len(rows) - 1
        ground.add_layer_on_bottom(GroundLayer(k_s=float(r["k_s"]), volumetric_heat_capacity=float(r["C"]) * 1e6,
                                               thickness=None if last else float(r["bottom"]) - float(r["top"])))
    return ground


register(Section(
    key="ground",
    group="Site",
    label="Ground",
    order=10,
    variants=(
        Variant(
            key="constant",
            label="Constant ground temperature",
            properties=(K_S, T_G, C_VOL, LAYERS),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: _ground(GroundConstantTemperature, v, T_g=v["T_g"]),
        ),
        Variant(
            key="flux",
            label="Surface temperature + heat flux",
            help="Ground temperature rises with depth because of the geothermal heat flux (as in EED).",
            properties=(K_S, T_SURFACE, C_VOL, LAYERS,
                        Property("flux", "Geothermal heat flux", 0.06, "W/m²", min=0.0, max=0.5, step=0.01)),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: _ground(GroundFluxTemperature, v, T_g=v["T_g"], flux=v["flux"]),
        ),
        Variant(
            key="gradient",
            label="Surface temperature + gradient",
            help="Ground temperature rises linearly with depth. Recommended for boreholes deeper than about 150 m.",
            properties=(K_S, T_SURFACE, C_VOL, LAYERS,
                        Property("gradient", "Geothermal gradient", 3.0, "K/100 m", min=0.0, max=10.0, step=0.1)),
            presets=ROCK, warnings=(_conductivity_warning,),
            build=lambda v: _ground(GroundTemperatureGradient, v, T_g=v["T_g"], gradient=v["gradient"]),
        ),
    ),
))
