from GHEtool import ConstantFlowRate

from .base import Property, Section, Variant
from .registry import register

register(Section(
    key="flow",
    label="Flow rate",
    order=50,
    variants=(
        Variant(
            key="constant_per_borehole",
            label="Constant flow per borehole",
            properties=(Property("mfr", "Mass flow rate per borehole", 0.3, "kg/s", min=0.01, max=5.0, step=0.01),),
            build=lambda v: ConstantFlowRate(mfr=v["mfr"]),
        ),
    ),
))
