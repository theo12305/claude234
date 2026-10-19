"""Well hydraulics: drawdown in the production wells and rise in the injection wells.

The wells pump and inject the same amount of water, so the field reaches a steady state within days. Thiem's
equation summed over all wells is then exact for a homogeneous aquifer: the radius of influence drops out because
the flows add up to zero. Unconfined aquifers get the Dupuit-Jacob correction for the thinner (or thicker) water
column, and every well its well loss C·Q².
"""
from __future__ import annotations

import math
from dataclasses import dataclass

RHO_W = 999.7  # kg/m³, water at 10 °C
C_W = 4.19e6  # J/(m³·K), volumetric heat capacity of water
G = 9.81


@dataclass(frozen=True)
class Well:
    x: float
    y: float
    q: float  # m³/s, positive pumps, negative injects


def head_change(wells: list[Well], x: float, y: float, transmissivity: float, r_well: float) -> float:
    """Drawdown (positive) or rise (negative) of the confined-equivalent head at (x, y) in metres: Thiem for each
    well, summed. At a well itself the distance is its radius."""
    total = sum(w.q for w in wells)
    if abs(total) > 1e-9 * max(abs(w.q) for w in wells):
        raise ValueError("Pumped and injected flow must be equal for the steady state.")
    s = 0.0
    for w in wells:
        r = max(math.hypot(x - w.x, y - w.y), r_well)
        s += w.q / (2 * math.pi * transmissivity) * math.log(1.0 / r)
    return s


def unconfined_drawdown(s_confined: float, thickness: float) -> float:
    """Real drawdown in an unconfined aquifer from the confined value (Jacob): s' = s − s²/2b. Inf when the well
    runs dry."""
    if 2 * s_confined >= thickness:
        return math.inf
    return thickness - math.sqrt(thickness ** 2 - 2 * thickness * s_confined)


def unconfined_rise(r_confined: float, thickness: float) -> float:
    """Real rise in an unconfined aquifer: the water column gets thicker, so the mound is lower than in a
    confined aquifer."""
    return math.sqrt(thickness ** 2 + 2 * thickness * r_confined) - thickness


@dataclass
class FieldHydraulics:
    drawdown: float  # m, largest drawdown in a production well, incl. well loss
    rise: float  # m, largest rise in an injection well, incl. well loss and clogging reserve
    drawdown_aquifer: float  # m, the part from the aquifer (without well loss)
    rise_aquifer: float
    well_loss_production: float
    well_loss_injection: float


def field_hydraulics(wells: list[Well], transmissivity: float, thickness: float, r_well: float, well_loss_c: float,
                     confined: bool, reserve: float) -> FieldHydraulics:
    """Drawdown and rise at the worst well. ``reserve`` multiplies the injection side for clogging (injection wells
    lose capacity over the years; 1.5 to 2 is usual)."""
    prod = [w for w in wells if w.q > 0]
    inj = [w for w in wells if w.q < 0]
    s_aq = max(head_change(wells, w.x, w.y, transmissivity, r_well) for w in prod)
    r_aq = max(-head_change(wells, w.x, w.y, transmissivity, r_well) for w in inj)
    loss_p = max(well_loss_c * w.q ** 2 for w in prod)
    loss_i = max(well_loss_c * w.q ** 2 for w in inj)
    if not confined:
        s_aq = unconfined_drawdown(s_aq, thickness)
        r_aq = unconfined_rise(r_aq, thickness)
    return FieldHydraulics(s_aq + loss_p, reserve * (r_aq + loss_i), s_aq, r_aq, loss_p, loss_i)


def entrance_velocity(q_well: float, r_borehole: float, screen_length: float) -> float:
    """Mean velocity of the water at the borehole wall along the screen [m/s]."""
    return abs(q_well) / (2 * math.pi * r_borehole * screen_length)


def pump_power(q: float, head: float, efficiency: float) -> float:
    """Electric power of the well pump [W] for flow q [m³/s] and total head [m]."""
    return RHO_W * G * q * head / efficiency


def cone(wells: list[Well], transmissivity: float, r_well: float, xs, ys):
    """Head change on a grid (confined-equivalent, without well losses), for the drawdown map."""
    import numpy as np
    xx, yy = np.meshgrid(xs, ys)
    s = np.zeros_like(xx)
    for w in wells:
        r = np.maximum(np.hypot(xx - w.x, yy - w.y), r_well)
        s += w.q / (2 * math.pi * transmissivity) * np.log(1.0 / r)
    return s


def cooper_jacob_fit(times_s, drawdowns, q: float, r: float) -> tuple[float, float]:
    """Transmissivity [m²/s] and storage coefficient from a pumping test (late-time straight line of drawdown
    against log time, Cooper-Jacob). ``r`` is the distance of the observation point (the well radius for the
    pumped well itself; then S is not reliable)."""
    import numpy as np
    t = np.asarray(times_s, float)
    s = np.asarray(drawdowns, float)
    keep = (t > 0) & np.isfinite(s)
    t, s = t[keep], s[keep]
    if len(t) < 3:
        raise ValueError("At least three readings are needed.")
    late = t >= np.quantile(t, 0.4)  # the straight line only holds once u is small
    slope, intercept = np.polyfit(np.log10(t[late]), s[late], 1)
    if slope <= 0:
        raise ValueError("The drawdown does not grow with time.")
    transmissivity = 2.303 * q / (4 * math.pi * slope)
    t0 = 10 ** (-intercept / slope)
    storage = 2.25 * transmissivity * t0 / r ** 2
    return float(transmissivity), float(storage)
