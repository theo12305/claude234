from dataclasses import dataclass

from GHEtool import CoaxialPipe, DoubleUTube, SingleUTube

from ..catalog import GROUT, PIPES
from .base import PresetGroup, Property, Section, Variant
from .registry import register

K_G = Property("k_g", "Grout thermal conductivity", 1.5, "W/(m·K)", min=0.1, max=5.0, step=0.1)
K_P = Property("k_p", "Pipe thermal conductivity", 0.42, "W/(m·K)", min=0.05, max=5.0, step=0.01)
U_PROPS = (
    K_G,
    Property("r_in_mm", "Pipe inner radius", 13.1, "mm", min=2.0, max=50.0, step=0.1),
    Property("r_out_mm", "Pipe outer radius", 16.0, "mm", min=3.0, max=60.0, step=0.5),
    K_P,
    Property("D_s_mm", "Distance pipe centre to borehole centre", 35.0, "mm", min=5.0, max=150.0, step=1.0),
)
U_PRESETS = (PresetGroup("Pipe", PIPES), PresetGroup("Grout", GROUT))


@dataclass(frozen=True)
class ConstantRb:
    """A borehole resistance measured in a thermal response test, used as it is."""
    Rb: float


def _radii_ok(v):
    if v["r_out_mm"] <= v["r_in_mm"]:
        return "Pipe outer radius must be larger than the inner radius."


def _u_kwargs(v):
    return dict(k_g=v["k_g"], r_in=v["r_in_mm"] / 1000, r_out=v["r_out_mm"] / 1000,
                k_p=v["k_p"], D_s=v["D_s_mm"] / 1000)


def _coaxial_ok(v):
    if not v["r_in_in_mm"] < v["r_in_out_mm"] < v["r_out_in_mm"] < v["r_out_out_mm"]:
        return "Coaxial radii must increase: inner pipe inside < inner pipe outside < outer pipe inside < outside."


register(Section(
    key="pipe",
    group="Borehole",
    label="Borehole heat exchanger",
    order=30,
    variants=(
        Variant("single_u", "Single U-tube", U_PROPS, checks=(_radii_ok,), presets=U_PRESETS,
                build=lambda v: SingleUTube(**_u_kwargs(v))),
        Variant("double_u", "Double U-tube", U_PROPS, checks=(_radii_ok,), presets=U_PRESETS,
                build=lambda v: DoubleUTube(**_u_kwargs(v))),
        Variant(
            "coaxial", "Coaxial",
            (
                K_G,
                Property("r_in_in_mm", "Inner pipe, inner radius", 22.0, "mm", min=2.0, max=100.0, step=0.5),
                Property("r_in_out_mm", "Inner pipe, outer radius", 25.0, "mm", min=3.0, max=100.0, step=0.5),
                Property("r_out_in_mm", "Outer pipe, inner radius", 48.7, "mm", min=4.0, max=150.0, step=0.5),
                Property("r_out_out_mm", "Outer pipe, outer radius", 55.0, "mm", min=5.0, max=150.0, step=0.5),
                K_P,
            ),
            checks=(_coaxial_ok,), presets=(PresetGroup("Grout", GROUT),),
            build=lambda v: CoaxialPipe(r_in_in=v["r_in_in_mm"] / 1000, r_in_out=v["r_in_out_mm"] / 1000,
                                        r_out_in=v["r_out_in_mm"] / 1000, r_out_out=v["r_out_out_mm"] / 1000,
                                        k_p=v["k_p"], k_g=v["k_g"], is_inner_inlet=True),
        ),
        Variant(
            "constant_rb", "Known borehole resistance (TRT)",
            (Property("Rb", "Effective borehole thermal resistance", 0.12, "m·K/W", min=0.01, max=1.0, step=0.005,
                      help="From a thermal response test. Inlet/outlet temperatures and pressure drop "
                           "cannot be calculated in this mode."),),
            help="Use a measured borehole resistance instead of calculating it from the pipe and fluid.",
            build=lambda v: ConstantRb(v["Rb"]),
        ),
    ),
))
