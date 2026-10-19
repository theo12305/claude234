from .base import Section, Variant
from .registry import register

register(Section(
    key="calculation",
    group="Design",
    system="closed",
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

