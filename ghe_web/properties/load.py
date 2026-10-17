from GHEtool import HourlyBuildingLoad, MonthlyGeothermalLoadAbsolute

from ..hourly import example_profile

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
        Variant(
            key="hourly_building",
            label="Hourly building demand",
            help="Heating and cooling demand of the building for every hour of a year. "
                 "The heat pump efficiency turns it into the load on the ground.",
            properties=(
                Property("profile", "Hourly demand", example_profile(), "kW", kind="hourly"),
                Property("scop", "SCOP heating", 4.0, min=1.0, max=10.0, step=0.1,
                         help="Seasonal efficiency of the heat pump in heating. "
                              "Ground extraction = heating × (1 − 1/SCOP)."),
                Property("seer", "SEER cooling", 20.0, min=1.0, max=1000.0, step=1.0,
                         help="Seasonal efficiency in cooling. Use a high value (e.g. 20+) for passive cooling. "
                              "Ground injection = cooling × (1 + 1/SEER)."),
                Property("simulation_period", "Simulation period", 20, "years", kind="int", min=1, max=100, step=1),
                Property("hourly_sizing", "Size with hourly resolution", True, kind="bool",
                         help="Slower but catches short peaks. Off: sizes on monthly values derived from the hours."),
            ),
            build=lambda v: HourlyBuildingLoad(
                heating_load=list(v["profile"]["heating"]),
                cooling_load=list(v["profile"]["cooling"]),
                simulation_period=int(v["simulation_period"]),
                efficiency_heating=v["scop"],
                efficiency_cooling=v["seer"]),
        ),
    ),
))
