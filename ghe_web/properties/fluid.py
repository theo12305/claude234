from GHEtool import TemperatureDependentFluidData

from ..catalog import FLUIDS
from .base import Property, Section, Variant
from .registry import register


def _concentration_ok(v):
    low, high = FLUIDS[v["name"]]
    if v["name"] != "Water" and not low <= v["percentage"] <= high:
        return f"GHEtool has data for {v['name']} between {low} and {high} %."


def _build(v):
    return TemperatureDependentFluidData(v["name"], 0 if v["name"] == "Water" else v["percentage"])


register(Section(
    key="fluid",
    group="Borehole",
    label="Fluid",
    order=40,
    variants=(
        Variant(
            key="antifreeze",
            label="Water / antifreeze mixture",
            properties=(
                Property("name", "Fluid", "MPG", kind="choice", options=tuple(FLUIDS),
                         help="MPG = propylene glycol, MEG = ethylene glycol, MEA = ethanol, MMA = methanol. "
                              "The others are commercial products."),
                Property("percentage", "Antifreeze share", 25.0, "% (mass)", min=0.0, max=65.0, step=1.0),
            ),
            checks=(_concentration_ok,),
            build=_build,
        ),
    ),
))
