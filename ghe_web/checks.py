"""Design check: every warning about a design in one list, each marked problem, warning or fine.

Input checks work before a calculation; result checks are added once the inputs have been sized. No Streamlit
code here, so the list can be tested and reused (e.g. in a report).
"""
from __future__ import annotations

from dataclasses import dataclass

from . import analysis, model, properties
from .geometry import closest_pair
from .i18n import fmt, t
from .properties import SectionInput

PROBLEM, WARNING, FINE = "problem", "warning", "fine"
K_USUAL = (1.0, 4.5)  # W/(m·K): most soils and rocks; outside this range the value is worth checking
VDI_MAX_W_PER_M = 60.0  # upper end of the VDI 4640 rule of thumb for extraction


@dataclass
class Check:
    level: str  # PROBLEM, WARNING or FINE
    title: str
    detail: str
    section: str | None = None  # the input section to go to for a fix


def _spacing(inputs: dict[str, SectionInput]) -> tuple[float, int, str] | None:
    """Smallest spacing, number of boreholes and a short description of where it is."""
    bf = inputs["borefield"]
    v = bf.values
    if bf.variant == "rectangular":
        n = v["N_1"] * v["N_2"]
        sides = [b for b, count in ((v["B_1"], v["N_1"]), (v["B_2"], v["N_2"])) if count > 1]
        return (min(sides), n, "") if sides else None
    pair = closest_pair(list(v["points"]))
    if pair is None:
        return None
    return pair[0], len(v["points"]), t("boreholes {a} and {b}", a=pair[1], b=pair[2])


def input_checks(inputs: dict[str, SectionInput]) -> list[Check]:
    out = []
    errors = model.validate(inputs)
    for key, msgs in errors.items():
        for msg in msgs:
            out.append(Check(PROBLEM, t(properties.get(key).label), msg, key))
    for source in (model.warnings(inputs), model.cross_warnings(inputs)):
        for key, msgs in source.items():
            for msg in msgs:
                out.append(Check(WARNING, t(properties.get(key).label), msg, key))
    if "borefield" in errors:
        return out

    ground = inputs["ground"].values
    k = ground.get("k_s")
    layered = (ground.get("layers") or {}).get("use")
    # an unusual value already has its own warning (from the ground section) above
    if k is not None and not layered and K_USUAL[0] <= k <= K_USUAL[1]:
        out.append(Check(FINE, t("Ground conductivity"),
                         t("{k:.1f} W/(m·K) is in the usual range of {lo:g} to {hi:g} W/(m·K).", k=k,
                           lo=K_USUAL[0], hi=K_USUAL[1]), "ground"))

    spacing = _spacing(inputs)
    if spacing is not None:
        b, n, where = spacing
        depth = inputs["borefield"].values["H"]
        where = f" ({where})" if where else ""
        if b < 5:
            out.append(Check(WARNING, t("Spacing between boreholes"),
                             t("The smallest spacing is {b:.1f} m{where}. VDI 4640 asks for at least 5 m (6 m for "
                               "boreholes deeper than 50 m).", b=b, where=where), "borefield"))
        elif b < 6 and depth > 50:
            out.append(Check(WARNING, t("Spacing between boreholes"),
                             t("The smallest spacing is {b:.1f} m{where} with {h:.0f} m long boreholes. VDI 4640 "
                               "asks for at least 6 m for boreholes deeper than 50 m.", b=b, where=where, h=depth),
                             "borefield"))
        else:
            out.append(Check(FINE, t("Spacing between boreholes"),
                             t("The smallest spacing is {b:.1f} m{where}.", b=b, where=where), "borefield"))
    return out


def result_checks(result: model.SizingResult, inputs: dict[str, SectionInput],
                  key: analysis.KeyResults) -> list[Check]:
    v = key.values
    out = []
    limits = inputs["limits"].values
    if v.get("margin_cold", 0) < -0.05 or v.get("margin_warm", 0) < -0.05:
        out.append(Check(PROBLEM, t("Temperature limits"),
                         t("The fluid goes beyond the limits: lowest {lo:.1f} °C (limit {t_min:g} °C), highest "
                           "{hi:.1f} °C (limit {t_max:g} °C). Make the boreholes longer or add boreholes.",
                           lo=v["t_min"], t_min=limits["T_min"], hi=v["t_max"], t_max=limits["T_max"]), "borefield"))
    else:
        out.append(Check(FINE, t("Temperature limits"),
                         t("The fluid stays between {lo:.1f} and {hi:.1f} °C (limits {t_min:g} and {t_max:g} °C).",
                           lo=v["t_min"], hi=v["t_max"], t_min=limits["T_min"], t_max=limits["T_max"]), "limits"))

    if "Re" in v:
        re = v["Re"]
        if re < analysis.LAMINAR_RE:
            out.append(Check(WARNING, t("Flow in the borehole"),
                             t("The flow is laminar (Re = {re:,.0f}), which raises the borehole resistance. A higher "
                               "flow rate, smaller pipes or less antifreeze make it turbulent and can shorten the "
                               "boreholes.", re=re), "flow"))
        else:
            out.append(Check(FINE, t("Flow in the borehole"),
                             t("Re = {re:,.0f} ({regime}) at the coldest fluid.", re=re, regime=analysis.regime(re)),
                             "flow"))

    freezing = getattr(result.borefield.borehole.fluid_data, "freezing_point", None)
    coldest = v.get("t_inlet_min", v.get("t_min"))
    if isinstance(freezing, (int, float)) and coldest is not None:
        name = inputs["fluid"].values.get("name", "")
        if coldest < freezing + 3:
            out.append(Check(PROBLEM if coldest < freezing else WARNING, t("Antifreeze"),
                             t("The coldest fluid ({cold:.1f} °C) is within 3 K of the freezing point "
                               "({freezing:.1f} °C). Use more antifreeze or a higher minimum temperature.",
                               cold=coldest, freezing=freezing), "fluid"))
        else:
            out.append(Check(FINE, t("Antifreeze"),
                             t("{fluid} protects to {freezing:.1f} °C; the coldest fluid is {cold:.1f} °C.",
                               fluid=t(name), freezing=freezing, cold=coldest), "fluid"))

    if "drift_k" in v:
        drift = v["drift_k"]
        if abs(drift) > 2:
            out.append(Check(WARNING, t("Ground balance"),
                             t("The yearly lowest temperature changes by {d:+.1f} K over the simulation: the ground "
                               "is out of balance ({imb:+,.0f} MWh per year). Cooling in summer or a larger spacing "
                               "helps.", d=drift, imb=v["imbalance_mwh"]), "load"))
        else:
            out.append(Check(FINE, t("Ground balance"),
                             t("The yearly lowest temperature changes by only {d:+.1f} K over the simulation.",
                               d=drift), "load"))

    w = v.get("w_per_m_extraction")
    if w is not None and w > VDI_MAX_W_PER_M:
        out.append(Check(WARNING, t("Specific heat extraction"),
                         t("{w:.0f} W/m at peak is above the VDI 4640 rule of thumb (30 to 60 W/m). The simulation "
                           "allows it, but check the peak load and the ground values.", w=w), "load"))

    depth = result.borehole_length + inputs["borefield"].values["D"]
    if depth > 100:
        out.append(Check(WARNING, t("Deeper than 100 m"),
                         t("The boreholes reach {d:.0f} m. In Germany drilling deeper than 100 m must be notified "
                           "to the mining authority (BBergG §127).", d=depth), "borefield"))
    return out


def counts(checks: list[Check]) -> dict[str, int]:
    return {level: sum(c.level == level for c in checks) for level in (PROBLEM, WARNING, FINE)}


def summary(checks: list[Check]) -> str:
    n = counts(checks)
    return fmt("{p} · {w} · {f}", p=t("{n} problem(s)", n=n[PROBLEM]), w=t("{n} warning(s)", n=n[WARNING]),
               f=t("{n} fine", n=n[FINE]))
