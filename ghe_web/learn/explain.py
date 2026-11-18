"""Explanations of a sized borefield in Learn mode, with the project's own numbers. No Streamlit here, so the tests
can check every sentence.

``why`` gives the four "why this length" steps, ``breakdown`` the parts of the temperature drop from the
undisturbed ground to the limiting fluid temperature, ``resistance_parts`` the borehole resistance split into
fluid film, pipe wall and grout.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import i18n
from ..core import analysis, model
from ..i18n import fmt
from .text import L


@dataclass(frozen=True)
class Step:
    title: str
    text: str  # Markdown
    sources: tuple[int, ...]


def why(result: model.SizingResult, key: analysis.KeyResults) -> list[Step]:
    """Four steps from the ground load to the length, with the project's numbers, in the current language."""
    v = key.values
    n, length, total = result.number_of_boreholes, result.borehole_length, result.total_length
    out, back = float(v.get("extraction_mwh") or 0), float(v.get("injection_mwh") or 0)
    steps = [Step(L("Ground load", "Erdseitige Last"),
                  fmt(L("After the heat pump efficiency the ground supplies **{out:,.1f} MWh/a** and absorbs "
                        "**{back:,.1f} MWh/a**; the net extraction is **{net:,.1f} MWh/a**.",
                        "Nach dem Wirkungsgrad der Wärmepumpe liefert der Untergrund **{out:,.1f} MWh/a** und nimmt "
                        "**{back:,.1f} MWh/a** auf; der Nettoentzug beträgt **{net:,.1f} MWh/a**."),
                      out=out, back=back, net=out - back), (4,))]
    w_m, kwh_m = float(v.get("w_per_m_extraction") or 0), float(v.get("kwh_per_m") or 0)
    steps.append(Step(L("Specific loading", "Spezifische Belastung"),
                      fmt(L("{n} × {h:,.1f} m = **{total:,.0f} m**: peak extraction **{w:,.1f} W/m**, annual "
                            "extraction **{kwh:,.0f} kWh/(m·a)**.",
                            "{n} × {h:,.1f} m = **{total:,.0f} m**: Spitzenentzug **{w:,.1f} W/m**, Jahresentzug "
                            "**{kwh:,.0f} kWh/(m·a)**."), n=n, h=length, total=total, w=w_m, kwh=kwh_m), (4,)))
    years = int(result.borefield.load.simulation_period)
    imbalance = out - back
    extremes = analysis.yearly_extremes(result)
    column = "Lowest" if imbalance >= 0 else "Highest"
    drift = float(extremes[column].iloc[-1] - extremes[column].iloc[0]) if len(extremes) > 1 else 0.0
    if abs(imbalance) < 0.05 * max(out, back, 1e-9):
        ground = fmt(L("Extraction and injection nearly balance (q_y ≈ 0), so the long-term term q_y·R_y vanishes; "
                       "the yearly extreme of the fluid changes by only {d:+.1f} K over {y} years.",
                       "Entzug und Eintrag sind nahezu ausgeglichen (q_y ≈ 0), der Langzeitterm q_y·R_y entfällt; "
                       "das Jahresextrem des Fluids ändert sich über {y} Jahre nur um {d:+.1f} K."), y=years, d=drift)
    else:
        ground = fmt(L("The net imbalance acts as a constant line sink of the whole field. Through the growing "
                       "g-function the yearly {side} of the fluid moves by **{d:+.1f} K** between year 1 and year {y}.",
                       "Die Nettobilanz wirkt als konstante Linienquelle des ganzen Feldes. Über die wachsende "
                       "g-Funktion verschiebt sich das jährliche {side} des Fluids zwischen Jahr 1 und Jahr {y} um "
                       "**{d:+.1f} K**."),
                     side=L("minimum", "Minimum") if imbalance > 0 else L("maximum", "Maximum"), y=years, d=drift)
    steps.append(Step(L("Long-term response", "Langzeitantwort"), ground, (1, 3)))
    b = analysis.coldest_breakdown(result)
    if b is not None:
        when = fmt(L("{month} of year {year}", "{month} des Jahres {year}"), month=i18n.long_month(b["month"]),
                   year=b["year"])
        parts = dict(b["parts"])
        slow = abs(parts.get("Long term", 0.0))
        fast = abs(parts.get("Peak (ground)", 0.0)) + abs(parts.get("Borehole", 0.0))
        regime = (L("The design is **drift-dominated**: the long-term term exceeds peak and borehole terms together.",
                    "Die Auslegung ist **driftdominiert**: der Langzeitterm übersteigt Spitzen- und Bohrlochterm "
                    "zusammen.") if slow > fast else
                  L("The design is **peak-dominated**: the peak terms (ground and R_b) exceed the long-term term.",
                    "Die Auslegung ist **spitzendominiert**: die Spitzenterme (Untergrund und R_b) übersteigen den "
                    "Langzeitterm."))
        if result.sizing_method == "check":
            text = fmt(L("In {when} the mean fluid temperature reaches {f:.1f} °C (limit {lim:.1f} °C). This is a "
                         "check of the given length, not a sizing. ",
                         "Im {when} erreicht die mittlere Fluidtemperatur {f:.1f} °C (Grenze {lim:.1f} °C). Das ist "
                         "eine Prüfung der vorgegebenen Länge, keine Auslegung. "),
                       when=when, f=b["fluid"], lim=b["limit"]) + regime
        else:
            text = fmt(L("The length is the root of T_f,extreme(H) = T_f,limit: in {when} the mean fluid temperature "
                         "reaches **{f:.1f} °C**, the limit of {lim:.1f} °C. ",
                         "Die Länge ist die Nullstelle von T_f,extrem(H) = T_f,Grenze: im {when} erreicht die "
                         "mittlere Fluidtemperatur **{f:.1f} °C**, die Grenze von {lim:.1f} °C. "),
                       when=when, f=b["fluid"], lim=b["limit"]) + regime
        steps.append(Step(L("Limiting condition", "Maßgebende Bedingung"), text, (1, 4)))
    return steps


PART_NAMES = {"Long term": ("Long term q_y·R_y", "Langzeit q_y·R_y"),
              "Month": ("Month q_m·R_m", "Monat q_m·R_m"),
                        "Peak (ground)": ("Peak q_h·R_h", "Spitze q_h·R_h"),
              "Borehole": ("Borehole q_h·R_b", "Bohrloch q_h·R_b")}


def breakdown(result: model.SizingResult) -> dict | None:
    """The waterfall from the undisturbed ground to the limiting fluid temperature, named in the current language.
    None for hourly results."""
    b = analysis.coldest_breakdown(result)
    if b is None:
        return None
    rows = [{"Part": L("Ground T_g", "Untergrund T_g"), "Start": 0.0, "End": b["t_ground"],
             "Change": b["t_ground"], "Kind": "ground"}]
    level = b["t_ground"]
    for name, change in b["parts"]:
        rows.append({"Part": L(*PART_NAMES[name]), "Start": level, "End": level + change, "Change": change,
                     "Kind": name})
        level += change
    rows.append({"Part": L("Fluid T_f", "Fluid T_f"), "Start": 0.0, "End": level, "Change": level, "Kind": "fluid"})
    return {**b, "rows": rows}


def resistance_parts(result: model.SizingResult, temperature: float = 0.0) -> list[tuple[str, float]] | None:
    """R_b split into fluid film, pipe wall and grout [m·K/W], for U-tubes. The film and wall resistances of the
    single pipes act in parallel (2 legs per U), the grout takes the rest of the effective R_b. An estimate for
    teaching: R_b itself comes from the multipole method, which does not split this way exactly."""
    bf = result.borefield
    pipe = bf.borehole.pipe_data
    legs = 2 * int(getattr(pipe, "number_of_pipes", 0) or 0)
    if not legs or not hasattr(pipe, "calculate_resistances") or not bf.borehole.flow_data:
        return None
    try:
        pipe.calculate_resistances(bf.borehole.fluid_data, bf.borehole.flow_data, temperature=temperature)
    except TypeError:
        pipe.calculate_resistances(bf.borehole.fluid_data, bf.borehole.flow_data)
    except Exception:
        return None
    film, wall = float(pipe.R_f) / legs, float(pipe.R_p) / legs
    rb = float(bf.Rb)
    grout = rb - film - wall
    if grout <= 0:
        return None
    return [(L("Fluid film", "Fluidgrenzschicht"), film), (L("Pipe wall", "Rohrwand"), wall),
            (L("Grout", "Verfüllung"), grout)]
