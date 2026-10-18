"""Predicts the layers under a site from nearby borehole logs and turns them into thermal properties.

No web code here. The method, in short:
1. Take the logged boreholes within a search radius, nearest first (at most ``max_boreholes``).
2. Walk down in steps of ``step`` metres. At each depth, every borehole that reaches it votes for its rock type
   with the weight 1 / distance² (inverse distance weighting). The rock type with the most weight wins; its share
   of the weight is the confidence at that depth.
3. Neighbouring steps with the same rock form a layer; layers thinner than ``min_thickness`` are merged into the
   thicker neighbour.
4. Below the deepest log the last rock type continues (marked as extrapolated). Without any logs, the rock of the
   geological map at the surface is used for the whole depth (low confidence).
5. Each layer gets its thermal conductivity and heat capacity from the rock table (VDI 4640); loose sediments
   above the groundwater table get their moist values, so such layers are split at the water table.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import rocks


@dataclass
class LogLayer:
    top: float  # m below ground
    bottom: float
    rock: str  # a rocks.NAMES entry
    text: str = ""  # the original description or code


@dataclass
class Borehole:
    name: str
    x: float  # m, ETRS89 / UTM 32N
    y: float
    layers: list[LogLayer]
    source: str = ""
    groundwater: float | None = None  # m below ground, when the log has it

    @property
    def depth(self) -> float:
        return max((l.bottom for l in self.layers), default=0.0)


@dataclass
class Layer:
    top: float
    bottom: float
    rock: str
    k_s: float  # W/(m·K)
    c: float  # MJ/(m³·K)
    confidence: float = 1.0  # 0..1, share of the weighted votes
    basis: str = ""  # where the layer comes from, e.g. "4 boreholes", "extrapolated", "geological map"

    @property
    def thickness(self) -> float:
        return self.bottom - self.top

    def row(self) -> dict:
        """As stored in the project file."""
        return {"top": round(self.top, 2), "bottom": round(self.bottom, 2), "rock": self.rock,
                "k_s": round(self.k_s, 3), "C": round(self.c, 3), "confidence": round(self.confidence, 2),
                "basis": self.basis}


@dataclass
class Prediction:
    layers: list[Layer]
    used: list[tuple[Borehole, float, float]] = field(default_factory=list)  # (borehole, distance, weight share)
    notes: list[str] = field(default_factory=list)
    surface_rock: str | None = None  # from the geological map

    def rows(self) -> list[dict]:
        return [layer.row() for layer in self.layers]


def distance(b: Borehole, x: float, y: float) -> float:
    return math.hypot(b.x - x, b.y - y)


def predict(boreholes: list[Borehole], x: float, y: float, depth: float, radius: float = 1000.0,
            max_boreholes: int = 8, power: float = 2.0, step: float = 0.5, min_thickness: float = 1.0,
            groundwater: float | None = None, surface_rock: str | None = None,
            bedrock: str | None = None) -> Prediction:
    """Layers from the surface to ``depth`` at (x, y). ``bedrock`` replaces the extrapolated rock below the
    deepest log, when the user knows it better."""
    logged = sorted(((b, distance(b, x, y)) for b in boreholes if b.layers), key=lambda t: t[1])
    near = [(b, d) for b, d in logged if d <= radius][:max_boreholes]
    notes = []
    if logged and not near:
        notes.append(f"The nearest log ({logged[0][0].name}) is {logged[0][1]:,.0f} m away, outside the search "
                     "radius. Increase the radius to use it.")
    if not near:
        rock = bedrock or surface_rock or rocks.UNKNOWN
        notes.append("No borehole logs within the search radius. The rock of the geological map at the surface "
                     "is used for the whole depth: please check it, e.g. against a log from the state's borehole "
                     "portal." if surface_rock else
                     "No borehole logs and no geological map data: enter the layers yourself.")
        votes = [(depth, rock, 0.2 if surface_rock else 0.0, "geological map" if surface_rock else "assumed")]
        layers = _merge_steps([(0.0, *votes[0][1:])], step=depth, end=depth)
        return Prediction(_with_thermal(layers, groundwater), [], notes, surface_rock)

    weights = {id(b): 1.0 / max(d, 5.0) ** power for b, d in near}  # 5 m floor: a log on the site is not infinite
    total = sum(weights.values())
    used = [(b, d, weights[id(b)] / total) for b, d in near]
    deepest = max(b.depth for b, _ in near)

    steps = []  # (top, rock, confidence, basis)
    n = max(1, math.ceil(depth / step))
    for i in range(n):
        z = min((i + 0.5) * step, depth)
        tally: dict[str, float] = {}
        reached = 0
        for b, _ in near:
            rock = _rock_at(b, z)
            if rock is not None:
                tally[rock] = tally.get(rock, 0.0) + weights[id(b)]
                reached += 1
        if tally:
            rock, w = max(tally.items(), key=lambda kv: kv[1])
            steps.append((i * step, rock, w / sum(tally.values()) * min(1.0, reached / 2),
                          f"{reached} log{'s' if reached > 1 else ''}"))
        else:
            last = steps[-1][1] if steps else (surface_rock or rocks.UNKNOWN)
            steps.append((i * step, bedrock or last, 0.3 if bedrock else 0.15, "extrapolated"))
    layers = _merge_steps(steps, step, depth)
    layers = _drop_thin(layers, min_thickness)
    if deepest < depth:
        notes.append(f"The deepest log nearby ends at {deepest:.0f} m. Below that, the last rock type is assumed "
                     "to continue" + (f" ({bedrock})." if bedrock else "; set the rock below the logs if you know it."))
    if groundwater is None:
        levels = [b.groundwater for b, _ in near if b.groundwater is not None]
        if levels:
            groundwater = sum(levels) / len(levels)
            notes.append(f"Groundwater table from the logs: about {groundwater:.1f} m below ground.")
    return Prediction(_with_thermal(layers, groundwater), used, notes, surface_rock)


def _rock_at(b: Borehole, z: float) -> str | None:
    for layer in b.layers:
        if layer.top <= z < layer.bottom:
            return layer.rock
    return None


def _merge_steps(steps, step: float, end: float) -> list[list]:
    """[top, bottom, rock, confidence (thickness weighted), basis] per run of equal rock."""
    out = []
    for i, (top, rock, conf, basis) in enumerate(steps):
        bottom = min(end, top + step)
        if out and out[-1][2] == rock and (out[-1][4] == "extrapolated") == (basis == "extrapolated"):
            prev = out[-1]
            prev[3] = (prev[3] * (prev[1] - prev[0]) + conf * (bottom - top)) / (bottom - prev[0])
            prev[1] = bottom
            if basis != prev[4] and basis != "extrapolated":
                prev[4] = _more_logs(prev[4], basis)
        else:
            out.append([top, bottom, rock, conf, basis])
    return out


def _more_logs(a: str, b: str) -> str:
    def n(s):
        return int(s.split()[0]) if s.split()[0].isdigit() else 0
    return a if n(a) >= n(b) else b


def _drop_thin(layers: list[list], min_thickness: float) -> list[list]:
    """Merges layers thinner than min_thickness into the thicker neighbour, thinnest first."""
    layers = [list(l) for l in layers]
    while len(layers) > 1:
        thin = [(l[1] - l[0], i) for i, l in enumerate(layers) if l[1] - l[0] < min_thickness]
        if not thin:
            break
        _, i = min(thin)
        neighbours = [j for j in (i - 1, i + 1) if 0 <= j < len(layers)]
        j = max(neighbours, key=lambda j: layers[j][1] - layers[j][0])
        a, b = sorted((i, j))
        keep = layers[j]
        layers[a:b + 1] = [[layers[a][0], layers[b][1], keep[2], keep[3], keep[4]]]
    # neighbours that now have the same rock become one layer
    out = []
    for l in layers:
        if out and out[-1][2] == l[2]:
            out[-1][1] = l[1]
        else:
            out.append(l)
    return out


def _with_thermal(layers: list[list], groundwater: float | None) -> list[Layer]:
    out = []
    for top, bottom, rock, conf, basis in layers:
        cuts = [top, bottom]
        if groundwater is not None and rocks.is_loose(rock) and top < groundwater < bottom:
            cuts = [top, groundwater, bottom]
        for a, b in zip(cuts, cuts[1:]):
            saturated = groundwater is None or a >= groundwater
            k, c = rocks.values(rock, saturated)
            out.append(Layer(a, b, rock, k, c, conf,
                             basis + ("" if saturated or not rocks.is_loose(rock) else ", above groundwater")))
    return out


# ---------------------------------------------------------------- stored layers (project file rows)

def effective(rows: list[dict], length: float, buried: float = 0.0) -> tuple[float, float]:
    """Thickness-weighted average conductivity and heat capacity along the borehole, from ``buried`` to
    ``buried + length``, like GHEtool does for layered ground. The last layer continues downwards."""
    if not rows:
        raise ValueError("No layers.")
    start, end = buried, buried + length
    k_sum = c_sum = 0.0
    for i, r in enumerate(rows):
        top, bottom = float(r["top"]), float(r["bottom"]) if i < len(rows) - 1 else math.inf
        part = max(0.0, min(end, bottom) - max(start, top))
        k_sum += part * float(r["k_s"])
        c_sum += part * float(r["C"])
    return float(k_sum / length), float(c_sum / length)


def contributions(rows: list[dict], length: float, buried: float = 0.0) -> list[dict]:
    """Per layer along the borehole: the length in it and its share of k·length (how much of the heat exchange
    it carries, roughly, in the steady state)."""
    start, end = buried, buried + length
    parts = []
    for i, r in enumerate(rows):
        top, bottom = float(r["top"]), float(r["bottom"]) if i < len(rows) - 1 else math.inf
        part = max(0.0, min(end, bottom) - max(start, top))
        if part > 0:
            parts.append({**r, "length": part, "kl": part * float(r["k_s"]),
                          "bottom_shown": min(bottom, end)})
    total = sum(p["kl"] for p in parts) or 1.0
    for p in parts:
        p["share"] = p["kl"] / total
    return parts


def check_rows(rows: list[dict]) -> list[str]:
    """Problems with a layer table: gaps, overlaps, missing or impossible values."""
    problems = []
    if not rows:
        return ["Layered ground is switched on, but there are no layers."]
    if abs(float(rows[0]["top"])) > 1e-6:
        problems.append("The first layer has to start at the surface (0 m).")
    for i, r in enumerate(rows):
        try:
            top, bottom, k, c = (float(r[key]) for key in ("top", "bottom", "k_s", "C"))
        except (KeyError, TypeError, ValueError):
            problems.append(f"Layer {i + 1}: every layer needs a depth, a conductivity and a heat capacity.")
            continue
        if bottom <= top:
            problems.append(f"Layer {i + 1}: the bottom ({bottom:g} m) has to be below the top ({top:g} m).")
        if not 0.1 <= k <= 10:
            problems.append(f"Layer {i + 1}: a conductivity of {k:g} W/(m·K) is outside 0.1 to 10.")
        if not 0.5 <= c <= 5:
            problems.append(f"Layer {i + 1}: a heat capacity of {c:g} MJ/(m³·K) is outside 0.5 to 5.")
        if i and abs(float(rows[i - 1]["bottom"]) - top) > 1e-6:
            problems.append(f"Layer {i + 1} starts at {top:g} m, but layer {i} ends at {rows[i - 1]['bottom']:g} m.")
    return problems


def rows_from_table(entries: list[tuple[float, str, float | None, float | None]]) -> list[dict]:
    """Layer rows from (bottom depth, rock, k or None, C or None) in order; tops follow from the row above and
    missing values come from the rock table."""
    rows, top = [], 0.0
    for bottom, rock, k, c in sorted(entries, key=lambda e: e[0]):
        dk, dc = rocks.values(rock)
        rows.append({"top": top, "bottom": float(bottom), "rock": rock,
                     "k_s": float(k) if k is not None and k == k else dk,
                     "C": float(c) if c is not None and c == c else dc,
                     "confidence": None, "basis": "entered"})
        top = float(bottom)
    return rows
