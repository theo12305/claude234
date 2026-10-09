from GHEtool import MonthlyGeothermalLoadAbsolute

from .base import Property, Section, Variant
from .registry import register

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

register(Section(
    key="load",
    label="Ground load",
    order=60,
    help="Heat taken from (extraction) and put into (injection) the ground.",
    variants=(
        Variant(
            key="monthly",
            label="Monthly energy and peaks",
            properties=(
                Property("baseload_extraction", "Extracted energy", kind="monthly", unit="kWh", min=0.0,
                         default=(46500, 44400, 37500, 29700, 19200, 0, 0, 0, 18300, 26100, 35100, 43200)),
                Property("baseload_injection", "Injected energy", kind="monthly", unit="kWh", min=0.0,
                         default=(4000, 8000, 8000, 8000, 12000, 16000, 32000, 32000, 16000, 12000, 8000, 4000)),
                Property("peak_extraction", "Peak extraction", kind="monthly", unit="kW", min=0.0,
                         default=(160, 142, 102, 55, 0, 0, 0, 0, 40.4, 85, 119, 136)),
                Property("peak_injection", "Peak injection", kind="monthly", unit="kW", min=0.0,
                         default=(0, 0, 40, 40, 45, 50, 80, 80, 50, 45, 40, 0)),
                Property("simulation_period", "Simulation period", 20, "years", kind="int", min=1, max=100, step=1),
            ),
            build=lambda v: MonthlyGeothermalLoadAbsolute(
                baseload_extraction=list(v["baseload_extraction"]),
                baseload_injection=list(v["baseload_injection"]),
                peak_extraction=list(v["peak_extraction"]),
                peak_injection=list(v["peak_injection"]),
                simulation_period=int(v["simulation_period"])),
        ),
    ),
))
