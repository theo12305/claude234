from .base import Property, Section, Variant
from .registry import register


def _rectangular(v):
    # Returned as keyword arguments for Borefield.create_rectangular_borefield.
    return ("create_rectangular_borefield", dict(
        N_1=v["N_1"], N_2=v["N_2"], B_1=v["B_1"], B_2=v["B_2"],
        H=v["H"], D=v["D"], r_b=v["r_b_mm"] / 1000))


register(Section(
    key="borefield",
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
                Property("H", "Borehole length", 100.0, "m", min=10.0, max=1000.0, step=5.0,
                         help="Start value; sizing calculates the required length."),
                Property("D", "Buried depth", 0.7, "m", min=0.0, max=20.0, step=0.1),
                Property("r_b_mm", "Borehole radius", 75.0, "mm", min=20.0, max=200.0, step=1.0),
            ),
            build=_rectangular,
        ),
    ),
))
