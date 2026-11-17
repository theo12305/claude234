"""Explanations of a sized borefield in Learn mode, with the project's own numbers. No Streamlit here, so the tests
can check every sentence.

``why`` gives the four "why this length" steps, ``breakdown`` the parts of the temperature drop from the
undisturbed ground to the limiting fluid temperature, ``resistance_parts`` the borehole resistance split into
fluid film, pipe wall and grout.
"""
from __future__ import annotations

from dataclasses import dataclass

from .. import analysis, i18n, model
from ..i18n import fmt
from .text import L


@dataclass(frozen=True)
class Step:
    title: str
    text: str  # Markdown
    sources: tuple[int, ...]


def why(result: model.SizingResult, key: analysis.KeyResults) -> list[Step]:
    """Four short steps from the load to the length, in the current language."""
    v = key.values
    n, length, total = result.number_of_boreholes, result.borehole_length, result.total_length
    out, back = float(v.get("extraction_mwh") or 0), float(v.get("injection_mwh") or 0)
    steps = [Step(L("The loads", "Die Lasten"),
                  fmt(L("The ground supplies **{out:,.1f} MWh** of heat per year and takes back **{back:,.1f} MWh** "
                        "from cooling.",
                        "Der Untergrund liefert **{out:,.1f} MWh** Wärme pro Jahr und nimmt **{back:,.1f} MWh** aus "
                        "der Kühlung zurück."), out=out, back=back), (4,))]
    w_m = float(v.get("w_per_m_extraction") or 0)
    steps.append(Step(L("The boreholes", "Die Sonden"),
                      fmt(L("{n} × {h:,.1f} m = **{total:,.0f} m** of borehole share it: on average "
                            "**{w:,.0f} W/m** while heating.",
                            "{n} × {h:,.1f} m = **{total:,.0f} m** Sonde teilen sich das: im Mittel **{w:,.0f} W/m** "
                            "beim Heizen."), n=n, h=length, total=total, w=w_m), (4,)))
    years = int(result.borefield.load.simulation_period)
    imbalance = out - back
    extremes = analysis.yearly_extremes(result)
    column = "Lowest" if imbalance >= 0 else "Highest"
    drift = float(extremes[column].iloc[-1] - extremes[column].iloc[0]) if len(extremes) > 1 else 0.0
    if abs(imbalance) < 0.05 * max(out, back, 1e-9):
        ground = fmt(L("Extraction and injection almost balance, so the ground hardly drifts over {y} years "
                       "({d:+.1f} K).",
                       "Entzug und Eintrag gleichen sich fast aus, der Untergrund driftet über {y} Jahre kaum "
                       "({d:+.1f} K)."), y=years, d=drift)
    elif imbalance > 0:
        ground = fmt(L("It loses **{x:,.1f} MWh** more per year than it gets back. Over {y} years the fluid's "
                       "yearly low drops by **{d:.1f} K**.",
                       "Er verliert pro Jahr **{x:,.1f} MWh** mehr, als er zurückbekommt. Über {y} Jahre sinkt das "
                       "Jahrestief des Fluids um **{d:.1f} K**."), x=imbalance, y=years, d=abs(drift))
    else:
        ground = fmt(L("It gets **{x:,.1f} MWh** more per year than it gives. Over {y} years the fluid's yearly "
                       "high rises by **{d:.1f} K**.",
                       "Er bekommt pro Jahr **{x:,.1f} MWh** mehr, als er abgibt. Über {y} Jahre steigt das "
                       "Jahreshoch des Fluids um **{d:.1f} K**."), x=-imbalance, y=years, d=abs(drift))
    steps.append(Step(L("The ground", "Der Untergrund"), ground, (1,)))
    b = analysis.coldest_breakdown(result)
    if b is not None:
        when = fmt(L("{month} of year {year}", "{month} im Jahr {year}"), month=i18n.long_month(b["month"]),
                   year=b["year"])
        side = L("lowest", "niedrigste") if b["cold"] else L("highest", "höchste")
        if result.sizing_method == "check":
            text = fmt(L("In {when} the mean fluid temperature reaches its {side} value, **{f:.1f} °C** (limit "
                         "{lim:.1f} °C). This is a check of the given length, not a sizing.",
                         "Im {when} erreicht die mittlere Fluidtemperatur ihren {side} Wert, **{f:.1f} °C** "
                         "(Grenze {lim:.1f} °C). Das ist eine Prüfung der vorgegebenen Länge, keine Auslegung."),
                       when=when, side=side, f=b["fluid"], lim=b["limit"])
        else:
            text = fmt(L("In {when} the mean fluid temperature reaches **{f:.1f} °C**, the limit of {lim:.1f} °C. "
                         "With shorter boreholes it would cross the limit: this sets the length.",
                         "Im {when} erreicht die mittlere Fluidtemperatur **{f:.1f} °C**, die Grenze von "
                         "{lim:.1f} °C. Mit kürzeren Sonden würde sie die Grenze überschreiten: das bestimmt die "
                         "Länge."), when=when, f=b["fluid"], lim=b["limit"])
        steps.append(Step(L("The limit", "Die Grenze"), text, (1, 4)))
    return steps


PART_NAMES = {"Long term": ("Years of imbalance", "Jahre der Bilanz"),
              "Month": ("This month", "Dieser Monat"),
              "Peak (ground)": ("Peak load (ground)", "Spitzenlast (Untergrund)"),
              "Borehole": ("Through the borehole (R_b)", "Durch das Bohrloch (R_b)")}


def breakdown(result: model.SizingResult) -> dict | None:
    """The waterfall from the undisturbed ground to the limiting fluid temperature, named in the current language.
    None for hourly results."""
    b = analysis.coldest_breakdown(result)
    if b is None:
        return None
    rows = [{"Part": L("Undisturbed ground", "Ungestörter Untergrund"), "Start": 0.0, "End": b["t_ground"],
             "Change": b["t_ground"], "Kind": "ground"}]
    level = b["t_ground"]
    for name, change in b["parts"]:
        rows.append({"Part": L(*PART_NAMES[name]), "Start": level, "End": level + change, "Change": change,
                     "Kind": name})
        level += change
    rows.append({"Part": L("Fluid", "Fluid"), "Start": 0.0, "End": level, "Change": level, "Kind": "fluid"})
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
