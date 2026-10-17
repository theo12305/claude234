from .base import Property, Section, Variant
from .registry import register

register(Section(
    key="calculation",
    group="Design",
    label="Calculation",
    order=75,
    variants=(
        Variant(
            key="size",
            label="Size the borehole length",
            help="Finds the shortest borehole length that keeps the fluid within the temperature limits.",
            properties=(),
            build=lambda v: {"mode": "size"},
        ),
        Variant(
            key="check",
            label="Check a given length",
            help="Uses the borehole length from the Borefield section as it is and shows the temperatures, "
                 "e.g. to check an existing field or a design from another tool.",
            properties=(),
            build=lambda v: {"mode": "check"},
        ),
    ),
))

register(Section(
    key="costs",
    group="Design",
    label="Costs",
    order=80,
    help="Rough investment estimate for comparing variants.",
    variants=(
        Variant(
            key="simple",
            label="Drilling and connection",
            properties=(
                Property("drilling_per_m", "Drilling and probe cost", 45.0, "€/m", min=0.0, max=1000.0, step=1.0,
                         help="Drilling, probe and grouting per metre of borehole."),
                Property("per_borehole", "Cost per borehole", 1500.0, "€", min=0.0, max=1e5, step=100.0,
                         help="Connection, trenching and manifold share per borehole."),
                Property("fixed", "Fixed cost", 10000.0, "€", min=0.0, max=1e7, step=1000.0,
                         help="Site setup, permits, thermal response test."),
            ),
            build=lambda v: v,
        ),
    ),
))
