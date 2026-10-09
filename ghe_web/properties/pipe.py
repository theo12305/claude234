from GHEtool import DoubleUTube, SingleUTube

from .base import Property, Section, Variant
from .registry import register

U_PROPS = (
    Property("k_g", "Grout thermal conductivity", 1.5, "W/(m·K)", min=0.1, max=5.0, step=0.1),
    Property("r_in_mm", "Pipe inner radius", 13.0, "mm", min=2.0, max=50.0, step=0.5),
    Property("r_out_mm", "Pipe outer radius", 16.0, "mm", min=3.0, max=60.0, step=0.5),
    Property("k_p", "Pipe thermal conductivity", 0.4, "W/(m·K)", min=0.05, max=5.0, step=0.05),
    Property("D_s_mm", "Distance pipe centre to borehole centre", 35.0, "mm", min=5.0, max=150.0, step=1.0),
)


def _radii_ok(v):
    if v["r_out_mm"] <= v["r_in_mm"]:
        return "Pipe outer radius must be larger than the inner radius."


def _u_kwargs(v):
    return dict(k_g=v["k_g"], r_in=v["r_in_mm"] / 1000, r_out=v["r_out_mm"] / 1000,
                k_p=v["k_p"], D_s=v["D_s_mm"] / 1000)


register(Section(
    key="pipe",
    label="Borehole heat exchanger",
    order=30,
    variants=(
        Variant("single_u", "Single U-tube", U_PROPS, checks=(_radii_ok,),
                build=lambda v: SingleUTube(**_u_kwargs(v))),
        Variant("double_u", "Double U-tube", U_PROPS, checks=(_radii_ok,),
                build=lambda v: DoubleUTube(**_u_kwargs(v))),
    ),
))
