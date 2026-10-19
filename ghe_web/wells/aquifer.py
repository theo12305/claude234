"""Hydraulic properties of rock types, and the aquifer read from the layer table of the ground section.

Hydraulic conductivity kf [m/s] and effective porosity are typical values (middle of the usual ranges in
DIN 18130 and the textbooks, e.g. Hölting & Coldewey). They are a first guess for planning: a pumping test gives
the real value, and kf varies by orders of magnitude within one rock type.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# rock type (names of strata.rocks) -> (kf [m/s], effective porosity [-])
HYDRAULIC = {
    "Made ground / fill": (1e-5, 0.15),
    "Topsoil / humus": (1e-6, 0.10),
    "Peat": (1e-7, 0.05),
    "Clay": (1e-9, 0.02),
    "Silt / loess": (1e-7, 0.05),
    "Sand": (2e-4, 0.20),
    "Gravel": (2e-3, 0.22),
    "Till / boulder clay": (1e-8, 0.03),
    "Claystone / siltstone": (1e-9, 0.01),
    "Shale / slate": (1e-9, 0.01),
    "Marl": (1e-8, 0.02),
    "Sandstone": (1e-5, 0.08),
    "Greywacke": (1e-7, 0.02),
    "Conglomerate / breccia": (1e-5, 0.08),
    "Limestone": (1e-5, 0.03),
    "Chalk": (1e-5, 0.03),
    "Dolomite": (1e-5, 0.03),
    "Anhydrite": (1e-9, 0.01),
    "Gypsum": (1e-7, 0.02),
    "Rock salt": (1e-12, 0.001),
    "Coal / lignite": (1e-7, 0.02),
}
HARD_ROCK = (1e-7, 0.01)  # crystalline rock and anything not listed: fractures only
AQUIFER_KF = 1e-5  # m/s: layers at least this permeable count as aquifer (DIN 18130: "durchlässig" from 1e-6)

# Presets for the aquifer section: kf [m/s] and effective porosity
SEDIMENTS = {
    "Gravel, clean": {"kf": 5e-3, "porosity": 0.25},
    "Sandy gravel": {"kf": 1e-3, "porosity": 0.22},
    "Coarse sand": {"kf": 5e-4, "porosity": 0.22},
    "Medium sand": {"kf": 2e-4, "porosity": 0.20},
    "Fine sand": {"kf": 5e-5, "porosity": 0.15},
    "Silty sand": {"kf": 1e-5, "porosity": 0.10},
    "Fractured sandstone": {"kf": 1e-5, "porosity": 0.05},
    "Karstified limestone": {"kf": 1e-4, "porosity": 0.03},
}


def hydraulic(rock: str) -> tuple[float, float]:
    return HYDRAULIC.get(rock, HARD_ROCK)


@dataclass
class AquiferGuess:
    top: float  # m below ground: top of the water-bearing part (the groundwater table in loose rock)
    bottom: float  # m below ground: first poorly permeable layer below
    kf: float  # m/s, thickness-weighted over the aquifer
    porosity: float
    rocks: list[str]

    @property
    def thickness(self) -> float:
        return self.bottom - self.top


def from_layers(rows: list[dict], groundwater_depth: float) -> AquiferGuess | None:
    """The first permeable stretch below the groundwater table in the layer table, with its average kf.
    None when there is none (the layers below the water table are all clay, rock without fractures, ...)."""
    top = bottom = None
    kf_sum = n_sum = 0.0
    found = []
    for i, r in enumerate(rows):
        a, b = max(float(r["top"]), groundwater_depth), float(r["bottom"])
        if b <= a:
            continue
        kf, n = hydraulic(r.get("rock", ""))
        if kf >= AQUIFER_KF:
            if top is None:
                top = a
            bottom = b
            kf_sum += kf * (b - a)
            n_sum += n * (b - a)
            if r.get("rock") not in found:
                found.append(r.get("rock"))
        elif top is not None:
            break
    if top is None or bottom - top <= 0:
        return None
    h = bottom - top
    return AquiferGuess(top, bottom, kf_sum / h, n_sum / h, found)


def sichardt_velocity(kf: float) -> float:
    """Largest allowed entrance velocity at the borehole wall [m/s] after Sichardt: √kf / 15."""
    return math.sqrt(kf) / 15
