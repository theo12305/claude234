from ..i18n import t
from .base import Property, Section, Variant
from .registry import register

register(Section(
    key="limits",
    group="Design",
    system="closed",
    label="Temperature limits",
    order=70,
    help="Allowed average fluid temperature in the borefield.",
    variants=(
        Variant(
            key="average_fluid",
            label="Average fluid temperature",
            properties=(
                Property("T_min", "Minimum fluid temperature", 0.0, "°C", min=-20.0, max=30.0, step=0.5),
                Property("T_max", "Maximum fluid temperature", 17.0, "°C", min=0.0, max=60.0, step=0.5),
            ),
            checks=(lambda v: None if v["T_max"] > v["T_min"]
                    else t("The maximum fluid temperature must be above the minimum."),),
            build=lambda v: v,
        ),
    ),
))
