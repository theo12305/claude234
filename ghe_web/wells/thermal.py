"""Thermal model of a well doublet in a groundwater flow.

* Recirculation: water from the injection wells is traced along the streamlines of the wells plus the regional
  groundwater flow. Streamlines that end in a production well bring the injected (cooled or warmed) water back,
  delayed by the thermal travel time: the hydraulic travel time × C_aquifer / (n · C_water), because the rock
  takes up heat as the water passes. The production temperature follows month by month.
* Plume: the yearly net heat put into the aquifer spreads downstream with the groundwater (planar advection and
  dispersion, continuous line source over the aquifer thickness).

Both leave out the heat exchange with the layers above and below the aquifer, so they are on the safe side.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .hydraulics import C_W, Well

SECONDS_PER_YEAR = 365.25 * 86400
SECONDS_PER_MONTH = SECONDS_PER_YEAR / 12


@dataclass
class Streamlines:
    arrival_hydraulic: np.ndarray  # s, travel time of each streamline that reaches a production well
    share: np.ndarray  # its share of the production flow
    paths: list[np.ndarray]  # a few traced paths (k × 2) for the map
    captured_fraction: float  # share of the injected water that comes back (within the traced time)

    @property
    def first_arrival(self) -> float | None:
        return float(self.arrival_hydraulic.min()) if len(self.arrival_hydraulic) else None


def _velocity(p: np.ndarray, wells: list[Well], thickness: float, porosity: float, darcy: float) -> np.ndarray:
    """Pore velocity [m/s] at points p (k × 2). x points downstream."""
    v = np.zeros_like(p)
    v[:, 0] = darcy / porosity
    for w in wells:
        d = p - (w.x, w.y)
        r2 = np.maximum((d ** 2).sum(axis=1), 1e-6)
        v += (-w.q / (2 * math.pi * thickness * porosity)) * d / r2[:, None]
    return v


def trace(wells: list[Well], thickness: float, porosity: float, darcy: float, t_max: float,
          per_well: int = 90, keep_paths: int = 24) -> Streamlines:
    """Streamlines from every injection well, until they reach a production well, leave the field or run longer
    than ``t_max`` [s]."""
    prod = np.array([(w.x, w.y) for w in wells if w.q > 0])
    inj = [w for w in wells if w.q < 0]
    q_prod = sum(w.q for w in wells if w.q > 0)
    allw = np.array([(w.x, w.y) for w in wells])
    span = max(float(np.ptp(allw[:, 0])), float(np.ptp(allw[:, 1])), 1.0)
    centre = allw.mean(axis=0)
    r0, r_capture = 0.3, 0.3
    starts, shares, t0 = [], [], []
    for w in inj:
        angles = (np.arange(per_well) + 0.5) * 2 * math.pi / per_well
        starts.append(np.c_[w.x + r0 * np.cos(angles), w.y + r0 * np.sin(angles)])
        shares += [-w.q / per_well / q_prod] * per_well
        t0 += [math.pi * thickness * porosity * r0 ** 2 / -w.q] * per_well  # time to get from the well to r0
    p = np.vstack(starts)
    share = np.array(shares)
    t = np.array(t0)
    active = np.ones(len(p), bool)
    arrived = np.zeros(len(p), bool)
    every = max(1, len(p) // keep_paths)
    tracked = np.arange(0, len(p), every)
    paths = {int(i): [p[i].copy()] for i in tracked}
    for _ in range(6000):
        if not active.any():
            break
        idx = np.flatnonzero(active)
        q = p[idx]
        dmin = np.sqrt(((q[:, None, :] - allw[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
        ds = np.clip(0.15 * dmin, 0.02, 0.05 * span + 0.5)
        v1 = _velocity(q, wells, thickness, porosity, darcy)
        speed = np.maximum(np.hypot(v1[:, 0], v1[:, 1]), 1e-15)
        dt = ds / speed
        mid = q + 0.5 * dt[:, None] * v1
        v2 = _velocity(mid, wells, thickness, porosity, darcy)
        q = q + dt[:, None] * v2
        p[idx] = q
        t[idx] += dt
        to_prod = np.sqrt(((q[:, None, :] - prod[None, :, :]) ** 2).sum(axis=2)).min(axis=1)
        hit = to_prod < r_capture
        gone = (np.hypot(*(q - centre).T) > 30 * span + 50) | (t[idx] > t_max)
        arrived[idx[hit]] = True
        active[idx[hit | gone]] = False
        for i in idx:
            if i in paths and (len(paths[i]) < 400):
                paths[i].append(p[i].copy())
    ok = arrived & (t <= t_max)
    return Streamlines(t[ok], share[ok], [np.array(v) for v in paths.values()], float(share[ok].sum()))


def critical_distance(q: float, thickness: float, darcy: float) -> float:
    """Distance between a production and an injection well (injection downstream) below which injected water
    flows back (Clyde & Madabhushi 1983): 2Q / (π b q)."""
    return math.inf if darcy <= 0 else 2 * q / (math.pi * thickness * darcy)


def doublet_breakthrough(q: float, thickness: float, porosity: float, distance: float) -> float:
    """Hydraulic travel time along the straight line between the wells of a doublet without regional flow
    [s]: π n b L² / 3Q (the textbook check for the tracing)."""
    return math.pi * porosity * thickness * distance ** 2 / (3 * q)


def production_temperature(spread: np.ndarray, delay_months: np.ndarray, share: np.ndarray) -> np.ndarray:
    """Change of the production temperature per month [K], from the change at injection ``spread`` [K per month,
    negative when heating] and the recirculating streamlines (delay in months, share of the production flow).

    The injection temperature is the production temperature plus the spread, so returning water lowers (or
    raises) the next injection too."""
    months = len(spread)
    delay = np.maximum(np.round(delay_months).astype(int), 0)
    now = share[delay == 0].sum()  # short circuit within the same month
    later = delay > 0
    d_later, w_later = delay[later], share[later]
    prod = np.zeros(months)
    inj = np.zeros(months)
    for m in range(months):
        back = 0.0
        if len(d_later):
            src = m - d_later
            ok = src >= 0
            back = float((w_later[ok] * inj[src[ok]]).sum())
        prod[m] = (back + now * spread[m]) / (1 - now) if now < 0.999 else math.copysign(99.0, spread[m] or 1)
        inj[m] = prod[m] + spread[m]
    return prod


def plume(heat_w: float, thickness: float, c_aquifer: float, k_aquifer: float, darcy: float, alpha_l: float,
          alpha_t: float, years: float, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """Temperature change [K] on a grid around a continuous heat source at (0, 0) after ``years``: planar advection
    and dispersion with thermal retardation, the source spread over the aquifer thickness. ``heat_w`` > 0 warms."""
    t_end = years * SECONDS_PER_YEAR
    v = darcy * C_W / c_aquifer  # velocity of the heat front
    d_l = k_aquifer / c_aquifer + alpha_l * v
    d_t = k_aquifer / c_aquifer + alpha_t * v
    xx, yy = np.meshgrid(xs, ys)
    taus = np.geomspace(3600.0, t_end, 160)
    out = np.zeros_like(xx)
    prev = None
    for tau in taus:
        f = np.exp(-((xx - v * tau) ** 2 / (4 * d_l * tau) + yy ** 2 / (4 * d_t * tau))) / tau
        if prev is not None:
            out += 0.5 * (f + prev[1]) * (tau - prev[0])
        prev = (tau, f)
    return heat_w / (4 * math.pi * thickness * c_aquifer * math.sqrt(d_l * d_t)) * out


def plume_length(heat_w: float, thickness: float, c_aquifer: float, k_aquifer: float, darcy: float, alpha_l: float,
                 alpha_t: float, years: float, threshold: float) -> float:
    """How far downstream of the injection wells the temperature change reaches ``threshold`` [K] [m]."""
    if heat_w == 0:
        return 0.0
    xs = np.unique(np.r_[np.geomspace(0.5, 5000, 400)])
    dt = plume(abs(heat_w), thickness, c_aquifer, k_aquifer, darcy, alpha_l, alpha_t, years, xs, np.array([0.0]))[0]
    above = xs[dt >= threshold]
    return float(above.max()) if len(above) else 0.0
