"""Help next to the inputs: which fields are for specialists (Simple / Expert mode), the typical range of a value,
and short side notes that translate a number into something familiar.

No web code here, so the tests can check it. Ranges are orientation, not limits: a value outside is allowed, the page
only points it out.
"""
from __future__ import annotations

from dataclasses import dataclass

from .i18n import fmt, t

# The choice on the start page: icon, name and a short description of each heat source.
HEAT_SOURCES = {"closed": ("⭕", "Borehole heat exchangers",
                           "Closed loop: probes usually 50 to 250 m deep with a water-glycol mixture. Possible almost "
                           "everywhere; needs a notification or permit."),
                "open": ("💧", "Groundwater wells",
                         "Open loop: a production and an injection well. Needs a productive aquifer at a shallow depth "
                         "and a permit from the water authority.")}

# (section, property) shown under "More options" in Simple mode. Every field stays on the page; Expert mode shows
# them all in line. Keys without a section ("*") count for every section.
ADVANCED = {
    ("borefield", "D"), ("borefield", "r_b_mm"),
    ("pipe", "k_p"), ("pipe", "D_s_mm"),
    ("flow", "pump_efficiency"), ("flow", "pump_hours"),
    ("load", "peak_extraction_hours"), ("load", "peak_injection_hours"), ("load", "scop_dhw"),
    ("aquifer", "alpha_l"), ("aquifer", "alpha_t"), ("aquifer", "direction"),
    ("wells", "well_loss"), ("wells", "reserve"), ("wells", "losses_m"), ("wells", "pump_efficiency"),
}


def is_advanced(section: str, key: str) -> bool:
    return (section, key) in ADVANCED or ("*", key) in ADVANCED


@dataclass(frozen=True)
class Typical:
    low: float
    high: float
    source: str  # shown under the bar


# Thermal conductivity range [W/(m·K)] per rock type of the "Rock type" drop-down (VDI 4640 part 1:2010, table A1;
# the drop-down fills in the recommended value of the same table).
ROCK_CONDUCTIVITY = {
    "Clay / silt, dry": (0.4, 1.0),
    "Clay / silt, water saturated": (1.1, 3.1),
    "Sand, dry": (0.3, 0.8),
    "Sand, moist": (1.0, 1.9),
    "Sand, water saturated": (2.0, 3.0),
    "Gravel, water saturated": (1.6, 2.5),
    "Till / loam": (1.1, 2.9),
    "Claystone / mudstone": (1.1, 3.4),
    "Marl": (1.5, 3.5),
    "Sandstone": (1.3, 5.1),
    "Limestone": (2.0, 3.9),
    "Dolomite": (3.0, 5.0),
    "Quartzite": (5.0, 6.0),
    "Granite": (2.1, 4.1),
    "Gneiss": (1.9, 4.0),
    "Mica schist": (1.5, 3.1),
    "Basalt": (1.3, 2.3),
    "Rock salt": (5.3, 6.4),
}

_GROUND_SOURCE = "usual in Germany"
TYPICAL: dict[str, Typical] = {
    "k_s": Typical(1.5, 3.5, _GROUND_SOURCE),
    "T_g": Typical(8.0, 14.0, _GROUND_SOURCE),
    "volumetric_heat_capacity": Typical(1.8, 2.8, "VDI 4640"),
    "k_g": Typical(0.8, 2.4, "grouts on the market"),
    "B_1": Typical(5.0, 10.0, "common spacing"),
    "B_2": Typical(5.0, 10.0, "common spacing"),
    "H": Typical(50.0, 250.0, "common borehole length"),
    "r_b_mm": Typical(57.5, 90.0, "common drilling diameters"),
    "percentage": Typical(20.0, 33.0, "common antifreeze share"),
    "scop": Typical(3.5, 5.5, "brine/water heat pumps"),
    "simulation_period": Typical(20.0, 50.0, "common design period"),
}


def typical(key: str, rock: str | None = None, label: str = "") -> Typical | None:
    """The typical range of a field; for the conductivity the range of the chosen rock type when there is one."""
    if key == "T_g" and label == "Ground surface temperature":
        return Typical(7.0, 12.0, "yearly mean in Germany")
    if key == "k_s" and rock in ROCK_CONDUCTIVITY:
        lo, hi = ROCK_CONDUCTIVITY[rock]
        return Typical(lo, hi, "VDI 4640 for {rock}")
    return TYPICAL.get(key)


def position(value: float, rng: Typical, low_limit: float | None, high_limit: float | None) -> tuple[float, float,
                                                                                                      float, float]:
    """Axis of the bar and where the typical band and the value sit on it, each from 0 to 1."""
    span = rng.high - rng.low
    lo, hi = rng.low - span, rng.high + span
    if low_limit is not None:
        lo = max(lo, low_limit)
    if high_limit is not None:
        hi = min(hi, high_limit)
    lo, hi = min(lo, value, rng.low), max(hi, value, rng.high)
    width = (hi - lo) or 1.0
    return lo, hi, (rng.low - lo) / width, (rng.high - lo) / width


def verdict(value: float, rng: Typical) -> str:
    """"typical", "low" or "high"."""
    if value < rng.low:
        return "low"
    if value > rng.high:
        return "high"
    return "typical"


def verdict_text(value: float, rng: Typical, rock: str | None = None) -> str:
    v = verdict(value, rng)
    source = t(rng.source, rock=t(rock)) if rock else t(rng.source)
    if v == "low":
        return t("lower than usual ({source}: {lo:g}–{hi:g}) – please check", source=source, lo=rng.low, hi=rng.high)
    if v == "high":
        return t("higher than usual ({source}: {lo:g}–{hi:g}) – please check", source=source, lo=rng.low, hi=rng.high)
    return t("typical ({source}: {lo:g}–{hi:g})", source=source, lo=rng.low, hi=rng.high)


def side_note(key: str, value: float, values: dict) -> str | None:
    """A short note that puts the value into everyday terms, or None."""
    if key == "mfr" and value > 0:
        # brine of about 1030 kg/m³: 1 kg/s ≈ 0.97 l/s ≈ 3.5 m³/h
        litres = value / 1.03
        return t("≈ {l:.2f} l/s = {m3:.2f} m³/h per borehole (water-glycol, about 1030 kg/m³)", l=litres,
                 m3=litres * 3.6)
    if key in ("peak_heating_kw",) and value > 0:
        # specific heat load of 40 W/m² (new, well insulated) to 100 W/m² (old, not refurbished)
        return t("≈ the heat load of {a:,.0f} m² (old building, 100 W/m²) to {b:,.0f} m² (new building, 40 W/m²) "
                 "of heated floor", a=value * 1000 / 100, b=value * 1000 / 40)
    if key == "annual_heating_mwh" and value > 0 and values.get("peak_heating_kw"):
        hours = value * 1000 / values["peak_heating_kw"]
        return t("{h:,.0f} full-load hours with the peak heating above (VDI 4640 assumes 1,800–2,400 h)", h=hours)
    if key == "H" and value + float(values.get("D") or 0) > 100:
        return t("Deeper than 100 m: the drilling must be reported to the mining authority (§ 127 BBergG).")
    return None
