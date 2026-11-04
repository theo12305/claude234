from GHEtool import HourlyBuildingLoad, MonthlyBuildingLoadAbsolute, MonthlyGeothermalLoadAbsolute

from ..catalog import MONTHLY_PROFILES
from ..hourly import example_profile
from .base import Property, Section, Variant
from .registry import register

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
HOURS_PER_MONTH = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)

PERIOD = Property("simulation_period", "Simulation period", 50, "years", kind="int", min=1, max=100, step=1)
PEAK_EXTRACTION_HOURS = Property("peak_extraction_hours", "Duration of the heating peak", 6, "h", min=1, max=24, step=1,
                                 help="How long the peak load lasts. GHEtool's default is 6 h.")
PEAK_INJECTION_HOURS = Property("peak_injection_hours", "Duration of the cooling peak", 6, "h", min=1, max=24, step=1)
SCOP = Property("scop", "SCOP heating", 4.0, min=1.0, max=10.0, step=0.1,
                help="Seasonal efficiency of the heat pump in heating. Ground extraction = heating × (1 − 1/SCOP). "
                     "Not used when Heat pump efficiency is set to depend on the fluid temperature.")
SEER = Property("seer", "SEER cooling", 20.0, min=1.0, max=1000.0, step=1.0,
                help="Seasonal efficiency in cooling. Use a high value (e.g. 20+) for passive cooling. "
                     "Ground injection = cooling × (1 + 1/SEER). Not used when Heat pump efficiency depends on the "
                     "fluid temperature.")
DHW = Property("dhw_mwh", "Domestic hot water demand", 0.0, "MWh/yr", min=0.0, max=1e5, step=1.0,
               scales_with_load=True, help="Spread evenly over the year.")
SCOP_DHW = Property("scop_dhw", "SCOP hot water", 3.0, min=1.0, max=10.0, step=0.1)


def _with_peak_durations(load, v):
    load.peak_extraction_duration = v["peak_extraction_hours"]
    load.peak_injection_duration = v["peak_injection_hours"]
    return load


def annual_energy_mwh(v) -> tuple[float, float]:
    """Yearly heating and cooling demand [MWh]: peak power × full-load hours."""
    return (v["peak_heating_kw"] * v["full_load_hours_heating"] / 1000,
            v["peak_cooling_kw"] * v["full_load_hours_cooling"] / 1000)


def from_annual_energy(saved: dict) -> dict:
    """Projects saved before the full-load hours: the yearly energy [MWh] becomes hours (energy / peak)."""
    out = {}
    for kind in ("heating", "cooling"):
        energy, peak = saved.get(f"annual_{kind}_mwh"), saved.get(f"peak_{kind}_kw")
        if energy is not None and f"full_load_hours_{kind}" not in saved:
            out[f"full_load_hours_{kind}"] = round(float(energy) * 1000 / float(peak), 1) if peak else 0.0
    return out


def _annual_to_monthly(v):
    """Yearly energy (peak × full-load hours) split over the months with a profile; peaks follow the profile
    shape."""
    def split(total_mwh, profile_name, peak_kw):
        shares = MONTHLY_PROFILES[profile_name]
        energy = [total_mwh * 1000 * s for s in shares]
        top = max(shares) or 1
        peaks = [max(peak_kw * s / top, e / h) if s > 0 else 0.0 for s, e, h in zip(shares, energy, HOURS_PER_MONTH)]
        return energy, peaks
    heat_mwh, cool_mwh = annual_energy_mwh(v)
    heat, heat_peak = split(heat_mwh, v["heating_profile"], v["peak_heating_kw"])
    cool, cool_peak = split(cool_mwh, v["cooling_profile"], v["peak_cooling_kw"])
    return heat, cool, heat_peak, cool_peak


def _annual_build(v):
    heat, cool, heat_peak, cool_peak = _annual_to_monthly(v)
    load = MonthlyBuildingLoadAbsolute(
        baseload_heating=heat, baseload_cooling=cool, peak_heating=heat_peak, peak_cooling=cool_peak,
        simulation_period=int(v["simulation_period"]), efficiency_heating=v["scop"], efficiency_cooling=v["seer"],
        dhw=v["dhw_mwh"] * 1000 if v["dhw_mwh"] else None, efficiency_dhw=v["scop_dhw"])
    return _with_peak_durations(load, v)

register(Section(
    key="load",
    group="Loads",
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
                PERIOD, PEAK_EXTRACTION_HOURS, PEAK_INJECTION_HOURS,
            ),
            build=lambda v: _with_peak_durations(MonthlyGeothermalLoadAbsolute(
                baseload_extraction=list(v["baseload_extraction"]),
                baseload_injection=list(v["baseload_injection"]),
                peak_extraction=list(v["peak_extraction"]),
                peak_injection=list(v["peak_injection"]),
                simulation_period=int(v["simulation_period"])), v),
        ),
        Variant(
            key="annual_building",
            label="Yearly building demand",
            help="Peak heating and cooling power of the building and their full-load hours; the yearly energy is "
                 "peak × full-load hours. It is split over the months with a profile, and the month with the largest "
                 "share gets the full peak.",
            properties=(
                Property("peak_heating_kw", "Peak heating load", 210.0, "kW", min=0.0, max=1e5, step=5.0,
                         scales_with_load=True),
                Property("full_load_hours_heating", "Full-load hours heating", 1905.0, "h/yr", min=0.0, max=8760.0,
                         step=50.0, help="Yearly heating energy divided by the peak heating load. VDI 4640 assumes "
                                         "1,800–2,400 h for heating only; with hot water up to about 2,400 h."),
                Property("heating_profile", "Heating profile", "Heating (office, GHEtool example)", kind="choice",
                         options=tuple(MONTHLY_PROFILES)),
                Property("peak_cooling_kw", "Peak cooling load", 80.0, "kW", min=0.0, max=1e5, step=5.0,
                         scales_with_load=True),
                Property("full_load_hours_cooling", "Full-load hours cooling", 1875.0, "h/yr", min=0.0, max=8760.0,
                         step=50.0, help="Yearly cooling energy divided by the peak cooling load."),
                Property("cooling_profile", "Cooling profile", "Cooling (office, GHEtool example)", kind="choice",
                         options=tuple(MONTHLY_PROFILES)),
                SCOP, SEER, DHW, SCOP_DHW, PERIOD, PEAK_EXTRACTION_HOURS, PEAK_INJECTION_HOURS,
            ),
            build=_annual_build,
        ),
        Variant(
            key="hourly_building",
            label="Hourly building demand",
            help="Heating and cooling demand of the building for every hour of a year. "
                 "The heat pump efficiency turns it into the load on the ground.",
            properties=(
                Property("profile", "Hourly demand", example_profile(), "kW", kind="hourly"),
                SCOP, SEER, DHW, SCOP_DHW, PERIOD,
                Property("hourly_sizing", "Size with hourly resolution", True, kind="bool",
                         help="Slower but catches short peaks. Off: sizes on monthly values derived from the hours."),
            ),
            build=lambda v: HourlyBuildingLoad(
                heating_load=list(v["profile"]["heating"]),
                cooling_load=list(v["profile"]["cooling"]),
                simulation_period=int(v["simulation_period"]),
                efficiency_heating=v["scop"],
                efficiency_cooling=v["seer"],
                dhw=v["dhw_mwh"] * 1000,
                efficiency_dhw=v["scop_dhw"]),
        ),
    ),
))
