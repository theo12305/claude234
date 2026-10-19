"""Heat source (boreholes or wells) and the inputs of open-loop systems: aquifer, water quality, wells, limits.

The calculation itself is in ``ghe_web.wells``; the builds here only turn the fields into SI values.
"""
from ..i18n import t
from ..wells.aquifer import SEDIMENTS
from .base import PresetGroup, Property, Section, Variant
from .registry import register

register(Section(
    key="system",
    group="Site",
    label="Heat source",
    order=0,
    help="Borehole heat exchangers circulate a fluid in closed pipes. Groundwater wells pump groundwater through "
         "the heat pump and return it to the aquifer through an injection well.",
    variants=(
        Variant(key="closed", label="Borehole heat exchangers (closed loop)", properties=(), build=lambda v: "closed"),
        Variant(key="open", label="Groundwater wells (open loop)", properties=(), build=lambda v: "open",
                help="Needs a productive aquifer at a shallow depth and a permit from the water authority "
                     "(wasserrechtliche Erlaubnis). Ground temperature and layers come from the section Ground."),
    ),
))

# ---------------------------------------------------------------- aquifer

KF = Property("kf", "Hydraulic conductivity kf", 1e-3, "m/s", min=1e-7, max=1e-1, step=1e-4, format="%.1e",
              help="From a pumping test if you have one; the drop-down gives typical values. Wells need about "
                   "1e-4 m/s or more.")
POROSITY = Property("porosity", "Effective porosity", 0.2, min=0.01, max=0.5, step=0.01,
                    help="The share of the volume the groundwater flows through. Sets how fast water and heat move.")
GRADIENT = Property("gradient", "Hydraulic gradient", 2.0, "‰", min=0.0, max=50.0, step=0.1,
                    help="Slope of the groundwater table, from the groundwater contour map of the state (in ‰: "
                         "2 ‰ = 2 m per km).")
DIRECTION = Property("direction", "Groundwater flow direction", 90.0, "°", min=0.0, max=360.0, step=5.0,
                     help="Direction the groundwater flows to, clockwise from north (90° = to the east). Only used "
                          "to draw the maps.")
ALPHA_L = Property("alpha_l", "Longitudinal dispersivity", 5.0, "m", min=0.0, max=100.0, step=0.5,
                   help="Spreading of the plume along the flow. Often taken as about 1/10 of the distance looked at.")
ALPHA_T = Property("alpha_t", "Transverse dispersivity", 0.5, "m", min=0.0, max=20.0, step=0.1,
                   help="Spreading across the flow, about 1/10 of the longitudinal value.")
WATER = Property("water_depth", "Depth to the groundwater", 5.0, "m", min=0.0, max=200.0, step=0.5,
                 help="Resting water level below ground at the site (lowest level of the year for the design).")
BOTTOM = Property("bottom", "Aquifer bottom", 25.0, "m", min=1.0, max=400.0, step=0.5,
                  help="Depth of the first poorly permeable layer below the aquifer (clay, marl, solid rock). The "
                       "wells usually end there.")
SEDIMENT = (PresetGroup("Aquifer type", SEDIMENTS, help="Typical values; kf varies a lot within one type."),)


def _bottom_below(top_key: str):
    def check(v):
        if v["bottom"] <= v[top_key] + 1:
            return t("The aquifer bottom ({b:g} m) must be at least 1 m below {what} ({a:g} m).", b=v["bottom"],
                     a=v[top_key], what=t("the groundwater") if top_key == "water_depth" else t("the aquifer top"))
    return check


def _low_kf(v):
    if v["kf"] < 1e-4:
        return t("kf = {kf:.1e} m/s is low for wells: each well yields little water and the drawdown is large. "
                 "Check closed-loop boreholes as well.", kf=v["kf"])


def _aquifer(v, confined: bool) -> dict:
    top = v["top"] if confined else v["water_depth"]
    return {"confined": confined, "water_depth": v["water_depth"], "top": top, "bottom": v["bottom"],
            "thickness": v["bottom"] - top, "kf": v["kf"], "porosity": v["porosity"],
            "gradient": v["gradient"] / 1000, "direction": v["direction"], "alpha_l": v["alpha_l"],
            "alpha_t": v["alpha_t"]}


register(Section(
    key="aquifer",
    group="Site",
    label="Aquifer",
    order=15,
    system="open",
    help="The water-bearing layer the wells pump from and inject into. Thermal conductivity and heat capacity are "
         "taken from Ground.",
    variants=(
        Variant(
            key="unconfined",
            label="Unconfined (free water table)",
            help="The groundwater table lies in the aquifer itself (typical for sand and gravel in river valleys).",
            properties=(WATER, BOTTOM, KF, POROSITY, GRADIENT, DIRECTION, ALPHA_L, ALPHA_T),
            presets=SEDIMENT, checks=(_bottom_below("water_depth"),), warnings=(_low_kf,),
            build=lambda v: _aquifer(v, False),
        ),
        Variant(
            key="confined",
            label="Confined (below a sealing layer)",
            help="A clay or marl layer covers the aquifer; the water level in a well rises above the aquifer top.",
            properties=(WATER, Property("top", "Aquifer top", 10.0, "m", min=0.0, max=400.0, step=0.5,
                                        help="Depth of the bottom of the sealing layer."),
                        BOTTOM, KF, POROSITY, GRADIENT, DIRECTION, ALPHA_L, ALPHA_T),
            presets=SEDIMENT, checks=(_bottom_below("top"),), warnings=(_low_kf,),
            build=lambda v: _aquifer(v, True),
        ),
    ),
))

# ---------------------------------------------------------------- water quality

register(Section(
    key="water_quality",
    group="Site",
    label="Groundwater quality",
    order=18,
    system="open",
    help="Iron and manganese with oxygen clog wells (ochre); chloride and a low pH corrode the heat exchanger.",
    variants=(
        Variant(key="none", label="No analysis yet", properties=(), build=lambda v: None,
                help="Have a sample analysed before planning: it decides whether wells work at the site and which "
                     "heat exchanger material is needed."),
        Variant(
            key="analysis",
            label="Water analysis",
            properties=(
                Property("iron", "Iron (dissolved)", 0.1, "mg/l", min=0.0, max=100.0, step=0.01),
                Property("manganese", "Manganese (dissolved)", 0.05, "mg/l", min=0.0, max=50.0, step=0.01),
                Property("oxygen", "Oxygen", 2.0, "mg/l", min=0.0, max=20.0, step=0.1),
                Property("ph", "pH", 7.2, min=3.0, max=12.0, step=0.1),
                Property("chloride", "Chloride", 40.0, "mg/l", min=0.0, max=20000.0, step=5.0),
                Property("sulfate", "Sulfate", 60.0, "mg/l", min=0.0, max=5000.0, step=5.0),
            ),
            build=lambda v: dict(v),
        ),
    ),
))

# ---------------------------------------------------------------- wells

ORIENTATIONS = ("Injection downstream", "Injection across the flow")
COMMON = (
    Property("d_bore_mm", "Drilling diameter", 400.0, "mm", min=100.0, max=2000.0, step=10.0,
             help="Diameter of the drilled hole with the gravel pack; the water enters the well there."),
    Property("dn_mm", "Screen diameter (DN)", 150.0, "mm", min=50.0, max=1000.0, step=25.0,
             help="Inner diameter of the screen and casing. DN 150 takes a 4 or 6 inch pump."),
    Property("orientation", "Position of the injection wells", ORIENTATIONS[0], kind="choice", options=ORIENTATIONS,
             help="Downstream is best: the injected water flows away from the production wells."),
    Property("spacing", "Spacing between wells of the same kind", 15.0, "m", min=2.0, max=500.0, step=1.0,
             help="Used when more than one production or injection well is needed; they stand in a row across "
                  "the flow."),
    Property("well_loss", "Well loss coefficient C", 1800.0, "s²/m⁵", min=0.0, max=1e6, step=100.0,
             help="Extra drawdown C·Q² in the well itself (screen, gravel pack). About 1800 s²/m⁵ for a properly "
                  "built well (Walton); from a step drawdown test if there is one."),
    Property("reserve", "Injection reserve for clogging", 1.5, min=1.0, max=5.0, step=0.1,
             help="Injection wells lose capacity over the years; the rise in the injection well is multiplied by "
                  "this factor. 1.5 to 2 is usual."),
    Property("losses_m", "Pipe and heat exchanger losses", 5.0, "m", min=0.0, max=100.0, step=0.5,
             help="Pressure loss of the pipes, valves and the heat exchanger at design flow, as water column "
                  "(10 m = 1 bar)."),
    Property("pump_efficiency", "Pump efficiency (wire to water)", 0.5, min=0.1, max=0.9, step=0.05),
    Property("border", "Distance to the parcel border downstream", 30.0, "m", min=0.0, max=10000.0, step=1.0,
             help="From the injection wells to the parcel border in the flow direction; the plume is checked "
                  "against it."),
)


def _wells(v, mode: str) -> dict:
    return {**dict(v), "mode": mode, "r_bore": v["d_bore_mm"] / 2000}


register(Section(
    key="wells",
    group="Borehole",
    label="Wells",
    order=25,
    system="open",
    help="Production wells pump the groundwater to the heat pump; injection wells return it to the aquifer.",
    variants=(
        Variant(
            key="size",
            label="Size the wells",
            help="Finds the number of wells and the shortest distance between production and injection that keeps "
                 "the production temperature and the water levels within the limits.",
            properties=COMMON + (
                Property("max_distance", "Largest possible distance between the wells", 60.0, "m", min=5.0,
                         max=2000.0, step=1.0, help="What fits on the parcel."),
            ),
            build=lambda v: _wells(v, "size"),
        ),
        Variant(
            key="check",
            label="Check given wells",
            properties=COMMON + (
                Property("n_production", "Production wells", 1, kind="int", min=1, max=20, step=1),
                Property("n_injection", "Injection wells", 1, kind="int", min=1, max=20, step=1),
                Property("distance", "Distance between production and injection", 20.0, "m", min=2.0, max=5000.0,
                         step=1.0),
            ),
            build=lambda v: _wells(v, "check"),
        ),
    ),
))

# ---------------------------------------------------------------- limits

register(Section(
    key="well_limits",
    group="Design",
    label="Limits for the groundwater",
    order=85,
    system="open",
    help="What the water authority and the heat pump allow. The values differ between the states: ask the "
         "Untere Wasserbehörde.",
    variants=(
        Variant(
            key="default",
            label="Temperature and water level limits",
            properties=(
                Property("spread", "Temperature spread at the heat pump", 4.0, "K", min=0.5, max=10.0, step=0.5,
                         help="How much the heat pump cools (or the cooling warms) the groundwater. Sets the flow: "
                              "a larger spread needs less water."),
                Property("t_inj_min", "Lowest injection temperature", 5.0, "°C", min=0.0, max=20.0, step=0.5),
                Property("t_inj_max", "Highest injection temperature", 20.0, "°C", min=5.0, max=40.0, step=0.5),
                Property("max_change", "Largest change from the natural temperature", 6.0, "K", min=0.5,
                         max=20.0, step=0.5, help="Of the injected water against the undisturbed groundwater."),
                Property("drift", "Allowed change of the production temperature", 1.0, "K", min=0.1, max=10.0,
                         step=0.1, help="Through injected water that flows back to the production wells, over the "
                                        "simulation period."),
                Property("plume_limit", "Plume limit at the parcel border", 1.0, "K", min=0.1, max=10.0, step=0.1,
                         help="Temperature change allowed at the parcel border (often 1 K)."),
                Property("freeboard", "Injection water level at least below ground", 1.0, "m", min=0.0, max=50.0,
                         step=0.5),
            ),
            build=lambda v: dict(v),
        ),
    ),
))
