from GHEtool import TemperatureDependentFluidData

from .base import Property, Section, Variant
from .registry import register

register(Section(
    key="fluid",
    label="Fluid",
    order=40,
    variants=(
        Variant(
            key="antifreeze",
            label="Water / antifreeze mixture",
            properties=(
                Property("name", "Fluid", "MPG", kind="choice",
                         options=("Water", "MPG", "MEG", "MEA", "MMA"),
                         help="MPG = propylene glycol, MEG = ethylene glycol."),
                Property("percentage", "Antifreeze share", 25.0, "% (mass)", min=0.0, max=60.0, step=1.0),
            ),
            build=lambda v: TemperatureDependentFluidData(
                v["name"], 0 if v["name"] == "Water" else v["percentage"]),
        ),
    ),
))
