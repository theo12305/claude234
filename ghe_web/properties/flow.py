from GHEtool import ConstantFlowRate

from .base import Property, Section, Variant
from .registry import register

register(Section(
    key="flow",
    group="Borehole",
    system="closed",
    label="Flow rate",
    order=50,
    variants=(
        Variant(
            key="constant_per_borehole",
            label="Constant flow per borehole",
            properties=(
                Property("mfr", "Mass flow rate per borehole", 0.3, "kg/s", min=0.01, max=5.0, step=0.01),
                Property("pump_efficiency", "Pump efficiency", 35.0, "%", min=5.0, max=90.0, step=1.0,
                         help="Wire-to-water efficiency of the circulation pump (motor and pump together). "
                              "Small brine circulators reach 25 to 40 %, large pumps 50 to 70 %. Only used for the "
                              "pump power and pump energy in the results."),
                Property("pump_hours", "Pump running hours per year", 4000.0, "h", min=0.0, max=8760.0, step=100.0,
                         help="How long the borefield pump runs in a year, roughly the heat pump's running hours. "
                              "Use 8760 if it runs all year. Only used for the pump energy in the results."),
            ),
            build=lambda v: ConstantFlowRate(mfr=v["mfr"]),
        ),
    ),
))
