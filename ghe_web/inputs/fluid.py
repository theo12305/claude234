from GHEtool import TemperatureDependentFluidData

from ghe_web.core.catalog import FLUIDS
from ghe_web.i18n import t
from ghe_web.inputs.base import Property, Section, Variant
from ghe_web.inputs.registry import register


def _concentration_ok(v):
    low, high = FLUIDS[v["name"]]
    if v["name"] != "Water" and not low <= v["percentage"] <= high:
        return t("GHEtool has data for {fluid} between {low} and {high} % by mass.", fluid=t(v["name"]), low=low,
                 high=high)


def _build(v):
    return TemperatureDependentFluidData(v["name"], 0 if v["name"] == "Water" else v["percentage"])


register(Section(
    key="fluid",
    group="Borehole",
    system="closed",
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
                Property("percentage", "Antifreeze concentration", 25.0, "% (mass)", min=0.0, max=75.0, step=1.0,
                         help="Share of antifreeze by mass. GHEtool converts it to volume for the commercial "
                              "products, whose data sheets give volume percentages."),
            ),
            checks=(_concentration_ok,),
            build=_build,
        ),
    ),
))
