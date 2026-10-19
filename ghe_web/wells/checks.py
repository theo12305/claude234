"""Design check for groundwater wells, in the same form as the borehole check (``ghe_web.checks``)."""
from __future__ import annotations

from .. import model, properties
from ..checks import FINE, PROBLEM, WARNING, Check
from ..i18n import t
from ..properties import SectionInput
from .design import Design

# Guide values for the groundwater (VDI 4640 Blatt 2 and the usual heat exchanger maker limits)
IRON, MANGANESE, OXYGEN = 0.2, 0.1, 2.0  # mg/l
CHLORIDE_STEEL, CHLORIDE_MAX = 100.0, 300.0  # mg/l: stainless steel heat exchangers; above that titanium
SULFATE = 250.0  # mg/l
PH_LOW, PH_HIGH = 6.5, 9.0


def input_checks(inputs: dict[str, SectionInput]) -> list[Check]:
    out = []
    for key, msgs in model.validate(inputs).items():
        for msg in msgs:
            out.append(Check(PROBLEM, t(properties.get(key).label), msg, key))
    for source in (model.warnings(inputs), model.cross_warnings(inputs)):
        for key, msgs in source.items():
            for msg in msgs:
                out.append(Check(WARNING, t(properties.get(key).label), msg, key))
    out += water_checks(inputs)
    return out


def water_checks(inputs: dict[str, SectionInput]) -> list[Check]:
    chosen = inputs.get("water_quality")
    if chosen is None or chosen.variant != "analysis":
        return [Check(WARNING, t("Groundwater quality"),
                      t("No water analysis yet. Iron, manganese and oxygen decide whether the wells clog; chloride "
                        "and pH decide the heat exchanger material."), "water_quality")]
    v = chosen.values
    out = []
    fe, mn, o2 = v["iron"], v["manganese"], v["oxygen"]
    if (fe > IRON or mn > MANGANESE) and o2 > OXYGEN:
        out.append(Check(PROBLEM, t("Clogging (ochre)"),
                         t("Iron {fe:g} mg/l and manganese {mn:g} mg/l together with {o2:g} mg/l oxygen precipitate "
                           "in the wells and the heat exchanger. Keep the system closed to air (pressure held, no "
                           "free fall in the injection well) or treat the water; ask a well builder.",
                           fe=fe, mn=mn, o2=o2), "water_quality"))
    elif fe > IRON or mn > MANGANESE:
        out.append(Check(WARNING, t("Clogging (ochre)"),
                         t("Iron {fe:g} mg/l or manganese {mn:g} mg/l is above the guide value ({fe_max:g} and "
                           "{mn_max:g} mg/l). Little oxygen keeps it dissolved: keep air out of the whole loop.",
                           fe=fe, mn=mn, fe_max=IRON, mn_max=MANGANESE), "water_quality"))
    else:
        out.append(Check(FINE, t("Clogging (ochre)"),
                         t("Iron and manganese are below the guide values."), "water_quality"))
    cl, ph, so4 = v["chloride"], v["ph"], v["sulfate"]
    if cl > CHLORIDE_MAX or ph < PH_LOW or ph > PH_HIGH:
        out.append(Check(PROBLEM if cl > CHLORIDE_MAX else WARNING, t("Corrosion and scaling"),
                         t("Chloride {cl:g} mg/l, pH {ph:g}: stainless steel heat exchangers are at risk. Use an "
                           "intermediate circuit with a titanium or suitable heat exchanger and ask the heat pump "
                           "maker.", cl=cl, ph=ph), "water_quality"))
    elif cl > CHLORIDE_STEEL or so4 > SULFATE:
        out.append(Check(WARNING, t("Corrosion and scaling"),
                         t("Chloride {cl:g} mg/l or sulfate {so4:g} mg/l is high: check the heat exchanger material "
                           "with the heat pump maker.", cl=cl, so4=so4), "water_quality"))
    else:
        out.append(Check(FINE, t("Corrosion and scaling"),
                         t("Chloride, sulfate and pH are in the usual range for stainless steel heat exchangers."),
                         "water_quality"))
    return out


def result_checks(d: Design, inputs: dict[str, SectionInput]) -> list[Check]:
    limits = inputs["well_limits"].values
    out = []
    if not d.feasible:
        out.append(Check(PROBLEM, t("No design found"),
                         t("No number of wells meets all limits within the largest possible distance of {d:g} m. "
                           "The figures below are for that distance.", d=d.distance), "wells"))

    if d.peak.drawdown > d.drawdown_allowed:
        out.append(Check(PROBLEM, t("Drawdown"),
                         t("The water level in the production well drops {s:.1f} m; at most {a:.1f} m are "
                           "possible. Add production wells or use a smaller flow (larger spread).",
                           s=d.peak.drawdown, a=d.drawdown_allowed), "wells"))
    else:
        out.append(Check(FINE, t("Drawdown"),
                         t("{s:.1f} m at peak flow ({a:.1f} m possible).", s=d.peak.drawdown, a=d.drawdown_allowed),
                         "wells"))

    if d.peak.rise > d.rise_allowed:
        out.append(Check(PROBLEM, t("Rise in the injection well"),
                         t("The water rises {r:.1f} m (with the clogging reserve); only {a:.1f} m are possible "
                           "before it gets too close to the surface. Add injection wells.",
                           r=d.peak.rise, a=max(d.rise_allowed, 0)), "wells"))
    else:
        out.append(Check(FINE, t("Rise in the injection well"),
                         t("{r:.1f} m with the clogging reserve ({a:.1f} m possible).", r=d.peak.rise,
                           a=d.rise_allowed), "wells"))

    if max(d.v_entrance_production, d.v_entrance_injection) > d.v_allowed:
        out.append(Check(PROBLEM, t("Entrance velocity"),
                         t("{v:.2f} mm/s at the borehole wall is more than the {a:.2f} mm/s Sichardt allows: sand "
                           "and fines get into the well. Use a larger drilling diameter or more wells.",
                           v=max(d.v_entrance_production, d.v_entrance_injection) * 1000, a=d.v_allowed * 1000),
                         "wells"))
    else:
        out.append(Check(FINE, t("Entrance velocity"),
                         t("{v:.2f} mm/s at the borehole wall ({a:.2f} mm/s allowed after Sichardt).",
                           v=max(d.v_entrance_production, d.v_entrance_injection) * 1000, a=d.v_allowed * 1000),
                         "wells"))

    if d.drift > limits["drift"]:
        out.append(Check(PROBLEM if d.mode == "check" else WARNING, t("Thermal short circuit"),
                         t("Injected water flows back and changes the production temperature by up to {dt:.1f} K "
                           "(allowed {a:g} K). Move the wells further apart or place the injection downstream.",
                           dt=d.drift, a=limits["drift"]), "wells"))
    elif d.breakthrough_years is not None and d.breakthrough_years < d.temperatures["year"].max():
        out.append(Check(FINE, t("Thermal short circuit"),
                         t("Injected water reaches the production well after {y:.1f} years, but the production "
                           "temperature changes by only {dt:.2f} K.", y=d.breakthrough_years, dt=d.drift), "wells"))
    else:
        out.append(Check(FINE, t("Thermal short circuit"),
                         t("No injected water reaches the production wells within the simulation period."), "wells"))

    lo, hi = d.t_injection_min, d.t_injection_max
    if lo < limits["t_inj_min"] or hi > limits["t_inj_max"] or \
            max(d.t_groundwater - lo, hi - d.t_groundwater) > limits["max_change"]:
        out.append(Check(PROBLEM, t("Injection temperature"),
                         t("The injected water is between {lo:.1f} and {hi:.1f} °C; allowed are {a:g} to {b:g} °C "
                           "and at most {c:g} K from the natural {tg:.1f} °C. A smaller spread helps.", lo=lo, hi=hi,
                           a=limits["t_inj_min"], b=limits["t_inj_max"], c=limits["max_change"], tg=d.t_groundwater),
                         "well_limits"))
    else:
        out.append(Check(FINE, t("Injection temperature"),
                         t("Between {lo:.1f} and {hi:.1f} °C.", lo=lo, hi=hi), "well_limits"))

    border = inputs["wells"].values["border"]
    reach = max(d.plume.values()) if d.plume else 0.0
    if reach > border:
        out.append(Check(WARNING, t("Temperature plume"),
                         t("A change of {k:g} K reaches {x:.0f} m downstream, beyond the parcel border at {b:g} m. "
                           "The water authority may ask for a plume model; the estimate leaves out the heat exchange "
                           "with the layers above and below, so the real plume is shorter.", k=limits["plume_limit"],
                           x=reach, b=border), "wells"))
    else:
        out.append(Check(FINE, t("Temperature plume"),
                         t("A change of {k:g} K stays within {x:.0f} m, inside the parcel border at {b:g} m.",
                           k=limits["plume_limit"], x=reach, b=border), "wells"))
    return out
