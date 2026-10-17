import math

import pygfunction as gt

from ..catalog import BOREHOLES
from ..geometry import closest_pair
from .base import PresetGroup, Property, Section, Variant
from .registry import register


def _rectangular(v):
    # Returned as keyword arguments for Borefield.create_rectangular_borefield.
    return ("create_rectangular_borefield", dict(
        N_1=v["N_1"], N_2=v["N_2"], B_1=v["B_1"], B_2=v["B_2"],
        H=v["H"], D=v["D"], r_b=v["r_b_mm"] / 1000))


def _custom(v):
    xs = [float(p[0]) for p in v["points"]]
    ys = [float(p[1]) for p in v["points"]]
    field = gt.borefield.Borefield(H=v["H"], D=v["D"], r_b=v["r_b_mm"] / 1000, x=xs, y=ys)
    return ("set_borefield", dict(borefield=field))


def _no_overlap(v):
    pair = closest_pair(v["points"])
    if pair and pair[0] < 2 * v["r_b_mm"] / 1000:
        return f"Boreholes {pair[1]} and {pair[2]} overlap ({pair[0]:.2f} m apart)."


def _rect_spacing_warning(v):
    if min(v["B_1"], v["B_2"]) < 4.5 and v["N_1"] * v["N_2"] > 1:
        return "Spacing below 4.5 m makes boreholes influence each other strongly; 5 to 8 m is common."


def _custom_spacing_warning(v):
    pair = closest_pair(v["points"])
    if pair and 2 * v["r_b_mm"] / 1000 <= pair[0] < 4.5:
        return f"Boreholes {pair[1]} and {pair[2]} are only {pair[0]:.1f} m apart; 5 to 8 m is common."


def _example_field():
    """Five curved rows of 12 boreholes, about 6 m apart: an irregular field to start from."""
    pts = [(r * math.cos(math.radians(10) + k * 6 / r), r * math.sin(math.radians(10) + k * 6 / r))
           for r in (40, 46, 52, 58, 64) for k in range(12)]
    x0, y0 = min(x for x, _ in pts), min(y for _, y in pts)
    return tuple((round(x - x0, 1), round(y - y0, 1)) for x, y in pts)


COMMON = (
    Property("H", "Borehole length", 100.0, "m", min=10.0, max=1000.0, step=5.0,
             help="Start value; sizing calculates the required length."),
    Property("D", "Buried depth", 0.7, "m", min=0.0, max=20.0, step=0.1),
    Property("r_b_mm", "Borehole radius", 75.0, "mm", min=20.0, max=200.0, step=1.0),
)


register(Section(
    key="borefield",
    group="Site",
    label="Borefield",
    order=20,
    variants=(
        Variant(
            key="rectangular",
            label="Rectangular field",
            properties=(
                Property("N_1", "Boreholes in x direction", 10, kind="int", min=1, max=50, step=1),
                Property("N_2", "Boreholes in y direction", 12, kind="int", min=1, max=50, step=1),
                Property("B_1", "Spacing in x direction", 6.0, "m", min=1.0, max=30.0, step=0.5),
                Property("B_2", "Spacing in y direction", 6.0, "m", min=1.0, max=30.0, step=0.5),
            ) + COMMON,
            presets=(PresetGroup("Drilling diameter", BOREHOLES),),
            warnings=(_rect_spacing_warning,),
            build=_rectangular,
        ),
        Variant(
            key="custom",
            label="Irregular field (shapefile)",
            help="Upload a point shapefile with one point per borehole, or edit the coordinates directly.",
            properties=(
                Property("points", "Borehole positions", _example_field(), "m", kind="points"),
            ) + COMMON,
            checks=(_no_overlap,),
            presets=(PresetGroup("Drilling diameter", BOREHOLES),),
            warnings=(_custom_spacing_warning,),
            build=_custom,
        ),
    ),
))
