"""The example projects of Learn mode and the parameters shown for them. No Streamlit here.

Each project is the app's default input set with a few values changed, so every number in Learn mode comes from the
same sizing (``model.size``) as a real project. ``PARAMETERS`` lists the inputs that Learn mode explains and lets the
user vary; ``sensitivity`` gives the local sensitivity of the required length to one of them.

The sensitivities of the three projects are stored in ``examples.json`` (``python -m tools.learn_examples`` writes it
again after a change here or in the sizing), so the page opens without waiting; ``tests/test_learn.py`` checks that
the stored lengths still match the sizing.
"""
from __future__ import annotations

import copy
import json
import pathlib
from dataclasses import dataclass, field

import numpy as np

from ..core import analysis, model
from ..inputs import SectionInput
from ..inputs import registry as input_registry
from ..i18n import t
from .text import L

DATA = pathlib.Path(__file__).with_name("examples.json")
COOLING_HOURS = 1000.0  # full-load hours of the cooling added in the regeneration study


@dataclass(frozen=True)
class Project:
    key: str
    title_en: str
    title_de: str
    lead_en: str  # one line under the title
    lead_de: str
    text_en: str  # what the project shows, Markdown
    text_de: str
    values: dict = field(default_factory=dict)  # (section, key) -> value, on top of the defaults

    @property
    def title(self) -> str:
        return L(self.title_en, self.title_de)

    @property
    def lead(self) -> str:
        return L(self.lead_en, self.lead_de)

    @property
    def text(self) -> str:
        return L(self.text_en, self.text_de)

    def inputs(self, changes: tuple = ()) -> dict[str, SectionInput]:
        """The full input set of the project (monthly sizing, building loads given as peak and full-load hours).
        ``changes``: (("section.key", value), ...) edited on the Learn page; the spacing applies to both directions."""
        inputs = model.default_inputs()
        inputs["load"].variant = "annual_building"
        variant = input_registry.get("load").variant("annual_building")
        values = dict(inputs["load"].values)
        for p in variant.properties:
            values.setdefault(p.key, p.default)
        inputs["load"].values = values
        for (section, key), value in self.values.items():
            inputs[section].values[key] = value
        for name, value in changes:
            section, key = name.split(".")
            inputs[section].values[key] = value
            if section == "borefield" and key == "B_1":
                inputs[section].values["B_2"] = value
        return inputs


PROJECTS: tuple[Project, ...] = (
    Project(
        "house", "Detached house, heating only", "Einfamilienhaus, nur Heizen",
        "2 boreholes · 10 kW · no regeneration", "2 Sonden · 10 kW · keine Regeneration",
        """A single-family house with a 10 kW brine/water heat pump (SCOP 4.5) and 2,000 full-load hours, two
boreholes 6 m apart. The ground is only cooled: the fluid temperature falls a little every year, but with two
boreholes the cooled zones barely overlap and the field approaches a near-steady state after a few years.
The length is set by the **peak in the coldest month**; the borehole thermal resistance carries a large share of the
temperature difference. Typical questions: how sensitive is the length to λ, to R_b and to the lower temperature
limit?""",
        """Ein Einfamilienhaus mit 10 kW Sole/Wasser-Wärmepumpe (JAZ 4,5) und 2.000 Volllaststunden, zwei Sonden im
Abstand von 6 m. Der Untergrund wird nur abgekühlt: die Fluidtemperatur sinkt jedes Jahr etwas, doch bei zwei
Sonden überlappen sich die abgekühlten Zonen kaum und das Feld nähert sich nach wenigen Jahren einem quasistationären
Zustand. Maßgebend ist die **Spitze im kältesten Monat**; der thermische Bohrlochwiderstand trägt einen großen Teil
der Temperaturdifferenz. Typische Fragen: wie empfindlich reagiert die Länge auf λ, auf R_b und auf die untere
Temperaturgrenze?""",
        {("borefield", "N_1"): 1, ("borefield", "N_2"): 2, ("borefield", "B_1"): 6.0, ("borefield", "B_2"): 6.0,
         ("ground", "k_s"): 2.2, ("ground", "T_g"): 10.5, ("pipe", "k_g"): 1.6, ("flow", "mfr"): 0.6,
         ("load", "peak_heating_kw"): 10.0, ("load", "full_load_hours_heating"): 2000.0,
         ("load", "peak_cooling_kw"): 0.0, ("load", "full_load_hours_cooling"): 0.0, ("load", "scop"): 4.5,
         ("limits", "T_min"): -1.5}),
    Project(
        "office", "Office with passive cooling", "Bürogebäude mit passiver Kühlung",
        "30 boreholes · 120 kW heating · 90 kW cooling", "30 Sonden · 120 kW Heizen · 90 kW Kühlen",
        """An office building with 120 kW heating (1,800 h, SCOP 4.2) and 90 kW free cooling (900 h) through the
borefield, 30 boreholes in a 5 × 6 grid at 6 m. Summer cooling returns about half of the extracted heat, so the
yearly imbalance is small and the long-term drift is weak. Both limits matter: the minimum in winter and, with
less heating or more cooling, the maximum in summer. Typical questions: how much length does the regeneration save,
and when does the design flip from heating- to cooling-dominated?""",
        """Ein Bürogebäude mit 120 kW Heizen (1.800 h, JAZ 4,2) und 90 kW freier Kühlung (900 h) über das Sondenfeld,
30 Sonden in einem 5 × 6-Raster mit 6 m Abstand. Die Sommerkühlung gibt etwa die Hälfte der entzogenen Wärme zurück,
die Jahresbilanz ist daher klein und die Langzeitdrift schwach. Beide Grenzen zählen: das Minimum im Winter und,
bei weniger Heizen oder mehr Kühlen, das Maximum im Sommer. Typische Fragen: wie viel Länge spart die Regeneration,
und wann kippt die Auslegung von heiz- zu kühldominiert?""",
        {("borefield", "N_1"): 5, ("borefield", "N_2"): 6, ("borefield", "B_1"): 6.0, ("borefield", "B_2"): 6.0,
         ("ground", "k_s"): 2.0, ("ground", "T_g"): 11.0, ("pipe", "k_g"): 1.6, ("flow", "mfr"): 0.7,
         ("load", "peak_heating_kw"): 120.0, ("load", "full_load_hours_heating"): 1800.0,
         ("load", "peak_cooling_kw"): 90.0, ("load", "full_load_hours_cooling"): 900.0, ("load", "scop"): 4.2,
         ("load", "seer"): 20.0, ("limits", "T_min"): -1.0}),
    Project(
        "quarter", "Residential quarter, large field", "Wohnquartier, großes Sondenfeld",
        "64 boreholes · 220 kW · heating only", "64 Sonden · 220 kW · nur Heizen",
        """A residential quarter with a central heat pump of 220 kW (1,900 h, SCOP 4.0) and no cooling, 64 boreholes
in an 8 × 8 grid at 6 m. Inner boreholes are surrounded by neighbours that extract heat as well; the thermal
interaction grows over decades and is captured by the field's g-function. Here the length is set by the **long-term
drift** in the last simulated year, not by the peak. Typical questions: what does the spacing or an open layout buy,
and how much regeneration would the field need?""",
        """Ein Wohnquartier mit zentraler Wärmepumpe von 220 kW (1.900 h, JAZ 4,0) ohne Kühlung, 64 Sonden in einem
8 × 8-Raster mit 6 m Abstand. Innere Sonden sind von Nachbarn umgeben, die ebenfalls Wärme entziehen; diese
thermische Wechselwirkung wächst über Jahrzehnte und steckt in der g-Funktion des Feldes. Hier bestimmt die
**Langzeitdrift** im letzten Simulationsjahr die Länge, nicht die Spitze. Typische Fragen: was bringen größerer
Abstand oder eine offene Anordnung, und wie viel Regeneration bräuchte das Feld?""",
        {("borefield", "N_1"): 8, ("borefield", "N_2"): 8, ("borefield", "B_1"): 6.0, ("borefield", "B_2"): 6.0,
         ("ground", "k_s"): 2.4, ("ground", "T_g"): 10.0, ("pipe", "k_g"): 2.0, ("flow", "mfr"): 0.7,
         ("load", "peak_heating_kw"): 220.0, ("load", "full_load_hours_heating"): 1900.0,
         ("load", "peak_cooling_kw"): 0.0, ("load", "full_load_hours_cooling"): 0.0, ("load", "scop"): 4.0,
         ("limits", "T_min"): -1.5}),
)
BY_KEY = {p.key: p for p in PROJECTS}


@dataclass(frozen=True)
class Parameter:
    section: str
    key: str
    term: str  # glossary key with the explanation
    group: str  # heading it is listed under
    kind: str = "rel"  # "rel": sensitivity per relative change; "abs": per absolute step (temperatures)
    step: float = 0.1  # +-10 % (rel) or +-1 K (abs) for the sensitivity
    lo: float | None = None  # range of the parameter study (factor for rel, offset for abs)
    hi: float | None = None
    label: tuple[str, str] | None = None  # (en, de) when the input's own label is too specific for this list
    symbol: str | None = None  # when the glossary term covers more than this parameter

    @property
    def name(self) -> str:
        return L(*self.label) if self.label else t(prop(self).label)


GROUPS = {"ground": ("Ground", "Untergrund"), "field": ("Borefield", "Sondenfeld"),
          "borehole": ("Borehole and fluid", "Bohrloch und Fluid"), "load": ("Loads", "Lasten"),
          "design": ("Design limits", "Auslegungsgrenzen")}

PARAMETERS: tuple[Parameter, ...] = (
    Parameter("ground", "k_s", "k_s", "ground", lo=0.5, hi=1.75),
    Parameter("ground", "T_g", "T_g", "ground", "abs", 1.0, -3.0, 3.0),
    Parameter("ground", "volumetric_heat_capacity", "volumetric_heat_capacity", "ground", lo=0.6, hi=1.4),
    Parameter("borefield", "B_1", "spacing", "field", lo=0.5, hi=2.5,
              label=("Borehole spacing", "Sondenabstand")),
    Parameter("borefield", "r_b_mm", "borehole_radius", "field", lo=0.8, hi=1.3),
    Parameter("pipe", "k_g", "k_g", "borehole", lo=0.4, hi=1.6),
    Parameter("flow", "mfr", "mfr", "borehole", lo=0.3, hi=2.0),
    Parameter("load", "peak_heating_kw", "peak_load", "load", lo=0.5, hi=1.5),
    Parameter("load", "full_load_hours_heating", "full_load_hours", "load", lo=0.6, hi=1.4),
    Parameter("load", "peak_cooling_kw", "peak_cooling", "load", lo=0.0, hi=2.0),
    Parameter("load", "scop", "scop", "load", lo=0.75, hi=1.3),
    Parameter("limits", "T_min", "limits", "design", "abs", 1.0, -3.0, 3.0, symbol="T_f,min"),
    Parameter("load", "simulation_period", "simulation_period", "design", lo=0.2, hi=2.0),
)
BY_PARAM = {(p.section, p.key): p for p in PARAMETERS}


def value(inputs: dict[str, SectionInput], p: Parameter) -> float:
    return float(inputs[p.section].values[p.key])


def prop(p: Parameter):
    """The input definition (label, unit) of a parameter."""
    section = input_registry.get(p.section)
    for variant in section.variants:
        for q in variant.properties:
            if q.key == p.key:
                return q
    raise KeyError(p.key)


def study_values(inputs: dict[str, SectionInput], p: Parameter, n: int = 9) -> tuple[float, ...]:
    """The values of a parameter study around the project's value."""
    now = value(inputs, p)
    if p.kind == "abs":
        values = now + np.linspace(p.lo, p.hi, n)
    elif now == 0:  # e.g. no cooling yet: from 0 to a typical value
        values = np.linspace(0.0, {"peak_cooling_kw": 0.6 * value(inputs, BY_PARAM[("load", "peak_heating_kw")])}
                             .get(p.key, 1.0), n)
    else:
        values = now * np.linspace(p.lo, p.hi, n)
    if p.key == "simulation_period":
        values = np.unique(np.maximum(1, np.round(values)))
    return tuple(round(float(v), 4) for v in values)


def prepared(inputs: dict[str, SectionInput], p: Parameter) -> dict[str, SectionInput]:
    """The inputs of a study: the full-load hours of cooling get a typical value when the cooling is varied from
    zero (otherwise a cooling peak would bring no energy)."""
    out = copy.deepcopy(inputs)
    if p.key == "peak_cooling_kw" and not out["load"].values.get("full_load_hours_cooling"):
        out["load"].values["full_load_hours_cooling"] = COOLING_HOURS
    return out


def study(inputs: dict[str, SectionInput], p: Parameter, values) -> "analysis.pd.DataFrame":
    """Required length per borehole for each value (``analysis.sweep``; spacing changes both directions)."""
    return analysis.sweep(prepared(inputs, p), p.section, p.key, values)


def sensitivity(inputs: dict[str, SectionInput], p: Parameter) -> float | None:
    """Local sensitivity of the required length by central differences. For ``rel`` parameters the elasticity
    (dL/L)/(dx/x), dimensionless; for ``abs`` parameters dL/dx in m per K. None when it cannot be formed."""
    now = value(inputs, p)
    if p.kind == "abs":
        lo, hi = now - p.step, now + p.step
    elif now == 0:
        return None
    else:
        lo, hi = now * (1 - p.step), now * (1 + p.step)
    df = study(inputs, p, [lo, now, hi])
    l_lo, l_now, l_hi = (float(x) for x in df["Length"])
    if not np.isfinite([l_lo, l_now, l_hi]).all():
        return None
    if p.kind == "abs":
        return (l_hi - l_lo) / (hi - lo)
    return ((l_hi - l_lo) / l_now) / ((hi - lo) / now)


def regeneration_study(inputs: dict[str, SectionInput], shares=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """Required length when a share of the yearly ground extraction is put back by cooling (passive, with the
    project's SEER and ``COOLING_HOURS`` full-load hours). Returns rows Share, Length."""
    import pandas as pd
    v = inputs["load"].values
    extraction = v["peak_heating_kw"] * v["full_load_hours_heating"] * (1 - 1 / v["scop"])  # kWh/yr into the HP
    rows = []
    for share in shares:
        trial = copy.deepcopy(inputs)
        cooling = share * extraction / (1 + 1 / v["seer"])  # building cooling energy that injects share × extraction
        trial["load"].values.update(peak_cooling_kw=cooling / COOLING_HOURS, full_load_hours_cooling=COOLING_HOURS)
        try:
            length = model.size(trial).borehole_length
        except Exception:
            length = float("nan")
        rows.append({"Share": share, "Length": length})
    return pd.DataFrame(rows)


def stored() -> dict:
    """The precomputed lengths and sensitivities (examples.json), or {} when missing."""
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def compute(project: Project) -> dict:
    """Length and the sensitivity of every parameter, as stored in examples.json."""
    inputs = project.inputs()
    result = model.size(inputs)
    sens = {f"{p.section}.{p.key}": sensitivity(inputs, p) for p in PARAMETERS}
    return {"length": round(result.borehole_length, 2),
            "sensitivity": {k: (None if v is None else round(v, 4)) for k, v in sens.items()}}
