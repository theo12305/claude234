"""Sizing and checking of an open-loop system: flow from the loads, wells from the hydraulics, well distance from
the thermal model. No web code here."""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .. import properties
from ..properties import SectionInput
from . import aquifer as aq
from .hydraulics import C_W, RHO_W, G, FieldHydraulics, Well, entrance_velocity, field_hydraulics, pump_power
from .thermal import SECONDS_PER_MONTH, SECONDS_PER_YEAR, Streamlines, critical_distance, plume_length, \
    production_temperature, trace

HOURS_PER_MONTH = np.array([744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744])
CANDIDATES = (5, 6, 8, 10, 12, 15, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 120, 140, 160, 180, 200,
              250, 300, 400, 500, 700, 1000, 1500, 2000)
MAX_WELLS = 20
SUMP = 1.0  # m of blank pipe below the screen
PUMP_SUBMERGENCE = 2.0  # m of water above the pump intake at the lowest level


def _build(inputs: dict[str, SectionInput], key: str):
    chosen = inputs[key]
    return properties.get(key).variant(chosen.variant).build(chosen.values)


@dataclass
class Loads:
    extraction: np.ndarray  # kWh per month (year 1), heat taken from the groundwater
    injection: np.ndarray  # kWh per month, heat put into the groundwater
    peak_extraction: np.ndarray  # kW per month
    peak_injection: np.ndarray
    heating: np.ndarray | None  # kWh per month delivered by the heat pump (building loads only), incl. hot water
    cooling: np.ndarray | None
    years: int


def loads(inputs: dict[str, SectionInput]) -> Loads:
    load = _build(inputs, "load")  # the fixed SCOP / SEER of the load section; no temperature-dependent COP here
    ext = np.asarray(load.monthly_baseload_extraction_simulation_period[:12], float)
    inj = np.asarray(load.monthly_baseload_injection_simulation_period[:12], float)
    pext = np.asarray(load.monthly_peak_extraction_simulation_period[:12], float)
    pinj = np.asarray(load.monthly_peak_injection_simulation_period[:12], float)
    heating = cooling = None
    if hasattr(load, "monthly_baseload_heating_simulation_period"):
        heating = np.asarray(load.monthly_baseload_heating_simulation_period[:12], float)
        dhw = getattr(load, "monthly_baseload_dhw_simulation_period", None)
        if dhw is not None and len(dhw):
            heating = heating + np.asarray(dhw[:12], float)
        cooling = np.asarray(load.monthly_baseload_cooling_simulation_period[:12], float)
    return Loads(ext, inj, pext, pinj, heating, cooling, int(load.simulation_period))


def groundwater_temperature(inputs: dict[str, SectionInput], depth: float) -> float:
    """Undisturbed temperature at ``depth`` from the ground section."""
    g = inputs["ground"]
    v = g.values
    if g.variant == "flux":
        k = v["k_s"]
        return v["T_g"] + v["flux"] / k * depth
    if g.variant == "gradient":
        return v["T_g"] + v["gradient"] / 100 * depth
    return v["T_g"]


def thermal_properties(inputs: dict[str, SectionInput], top: float, bottom: float) -> tuple[float, float]:
    """Conductivity [W/(m·K)] and volumetric heat capacity [J/(m³·K)] of the aquifer, from the layers when they
    are in use."""
    from ..properties.ground import layered
    from ..strata.predict import effective
    v = inputs["ground"].values
    if layered(v):
        k, c = effective(list(v["layers"]["rows"]), bottom - top, top)
        return k, c * 1e6
    return v["k_s"], v["volumetric_heat_capacity"] * 1e6


def layout(n_prod: int, n_inj: int, distance: float, q: float, orientation: str, spacing: float) -> list[Well]:
    """Wells in local coordinates, x downstream: production wells in a row across the flow at x = 0, injection
    wells downstream at x = distance, or beside them across the flow."""
    def row(n):
        return [spacing * (i - (n - 1) / 2) for i in range(n)]
    wells = [Well(0.0, y, q / n_prod) for y in row(n_prod)]
    if orientation == "Injection across the flow":
        offset = distance + spacing * ((n_prod - 1) + (n_inj - 1)) / 2
        wells += [Well(0.0, offset + y - row(n_inj)[0] - spacing * (n_inj - 1) / 2, -q / n_inj) for y in row(n_inj)]
    else:
        wells += [Well(distance, y, -q / n_inj) for y in row(n_inj)]
    return wells


@dataclass
class Screen:
    top: float
    bottom: float
    depth: float  # depth of the well (to the aquifer bottom)

    @property
    def length(self) -> float:
        return self.bottom - self.top


@dataclass
class Design:
    """Everything the results page shows."""
    mode: str  # "size" or "check"
    n_production: int
    n_injection: int
    distance: float
    wells: list[Well]
    screen: Screen
    t_groundwater: float
    q_peak: float  # m³/s, all production wells together
    q_operating: float  # m³/s, average flow in the months the system runs
    volume_year: float  # m³
    peak: FieldHydraulics  # at peak flow
    mean: FieldHydraulics  # at the operating flow
    drawdown_allowed: float
    rise_allowed: float
    v_entrance_production: float
    v_entrance_injection: float
    v_allowed: float
    pump_head: float
    pump_power: float  # W, all production pumps at peak flow
    pump_depth: float
    pump_energy_year: float  # kWh
    darcy: float  # m/s
    critical_distance: float
    k_aquifer: float
    c_aquifer: float
    retardation: float
    streamlines: Streamlines
    temperatures: pd.DataFrame  # per month: year, month, production, injection
    drift: float  # K, largest change of the production temperature
    breakthrough_years: float | None
    heat_net_w: float  # yearly mean heat put into the aquifer (negative: cooled)
    plume: dict[int, float]  # years -> plume length downstream [m] at the plume limit
    monthly: pd.DataFrame
    spf: float | None
    hp_electricity_year: float | None
    tried: list[dict] = field(default_factory=list)
    loads: Loads | None = None
    feasible: bool = True

    @property
    def q_peak_well(self) -> float:
        return self.q_peak / self.n_production

    @property
    def t_production_min(self) -> float:
        return float(self.temperatures["production"].min())

    @property
    def t_injection_min(self) -> float:
        active = self.temperatures[self.temperatures["active"]]
        return float(active["injection"].min()) if len(active) else self.t_groundwater

    @property
    def t_injection_max(self) -> float:
        active = self.temperatures[self.temperatures["active"]]
        return float(active["injection"].max()) if len(active) else self.t_groundwater


def _screen(aquifer: dict, drawdown_allowed: float) -> Screen:
    if aquifer["confined"]:
        top = aquifer["top"]
    else:  # the screen starts below the lowest water level in the pumped well, with 1 m to spare
        top = aquifer["water_depth"] + drawdown_allowed + 1.0
    bottom = max(aquifer["bottom"] - SUMP, top + 1.0)
    return Screen(top, bottom, aquifer["bottom"])


def allowed_drawdown(aquifer: dict) -> float:
    """Unconfined: a third of the saturated thickness (beyond that the yield hardly grows and the screen dries).
    Confined: down to 1 m above the aquifer top, at least a third of the thickness."""
    if aquifer["confined"]:
        return max(aquifer["top"] - aquifer["water_depth"] - 1.0, aquifer["thickness"] / 3)
    return aquifer["thickness"] / 3


def _hydraulics(wells, aquifer, w) -> FieldHydraulics:
    transmissivity = aquifer["kf"] * aquifer["thickness"]
    return field_hydraulics(wells, transmissivity, aquifer["thickness"], w["r_bore"], w["well_loss"],
                            aquifer["confined"], w["reserve"])


def _hydraulic_ok(h: FieldHydraulics, q, n_p, n_i, screen, aquifer, w, limits) -> list[str]:
    reasons = []
    v_allowed = aq.sichardt_velocity(aquifer["kf"])
    if h.drawdown > allowed_drawdown(aquifer):
        reasons.append("drawdown")
    if h.rise > aquifer["water_depth"] - limits["freeboard"]:
        reasons.append("rise")
    if entrance_velocity(q / n_p, w["r_bore"], screen.length) > v_allowed:
        reasons.append("entrance production")
    if entrance_velocity(q / n_i, w["r_bore"], screen.length) * w["reserve"] > v_allowed:
        reasons.append("entrance injection")
    return reasons


def _thermal(wells, aquifer, k_aq, c_aq, q_op, spread_month, active_month, years, t_gw):
    darcy = aquifer["kf"] * aquifer["gradient"]
    retardation = c_aq / (aquifer["porosity"] * C_W)
    t_max = years * SECONDS_PER_YEAR / retardation
    scaled = [Well(x.x, x.y, x.q * q_op / sum(v.q for v in wells if v.q > 0)) for x in wells]
    lines = trace(scaled, aquifer["thickness"], aquifer["porosity"], darcy, t_max)
    delay = lines.arrival_hydraulic * retardation / SECONDS_PER_MONTH
    spread = np.tile(spread_month, years)
    dev = production_temperature(spread, delay, lines.share)
    active = np.tile(active_month, years)
    temps = pd.DataFrame({"year": np.repeat(np.arange(1, years + 1), 12), "month": np.tile(np.arange(1, 13), years),
                          "production": t_gw + dev, "injection": t_gw + dev + spread, "active": active})
    first = lines.first_arrival
    breakthrough = first * retardation / SECONDS_PER_YEAR if first is not None else None
    return lines, temps, float(np.abs(dev).max()) if len(dev) else 0.0, breakthrough, darcy, retardation


def size(inputs: dict[str, SectionInput]) -> Design:
    aquifer = _build(inputs, "aquifer")
    w = _build(inputs, "wells")
    limits = _build(inputs, "well_limits")
    ld = loads(inputs)
    spread = limits["spread"]

    flow_energy = ld.extraction + ld.injection  # kWh moved through the heat exchanger per month
    volumes = flow_energy * 3.6e6 / (C_W * spread)
    peak_kw = max(float(ld.peak_extraction.max()), float(ld.peak_injection.max()))
    q_peak = peak_kw * 1000 / (C_W * spread)
    active = volumes > 0
    q_op = float(volumes.sum() / (HOURS_PER_MONTH[active].sum() * 3600)) if active.any() else 0.0
    if q_peak <= 0 or q_op <= 0:
        raise ValueError("The load is zero: there is nothing to size.")
    with np.errstate(invalid="ignore", divide="ignore"):
        spread_month = np.where(active, (ld.injection - ld.extraction) / np.where(active, flow_energy, 1) * spread, 0.0)

    s_allow = allowed_drawdown(aquifer)
    screen = _screen(aquifer, s_allow)
    t_gw = groundwater_temperature(inputs, (screen.top + screen.bottom) / 2)
    k_aq, c_aq = thermal_properties(inputs, aquifer["top"], aquifer["bottom"])

    tried = []
    feasible = True
    if w["mode"] == "check":
        n_p, n_i, dist = w["n_production"], w["n_injection"], w["distance"]
        wells = layout(n_p, n_i, dist, q_peak, w["orientation"], w["spacing"])
        thermal = _thermal(wells, aquifer, k_aq, c_aq, q_op, spread_month, active, ld.years, t_gw)
    else:
        distances = [d for d in CANDIDATES if d < w["max_distance"]] + [w["max_distance"]]
        choice = None
        for dist in distances:
            n_p, n_i, wells, reasons = _fewest_wells(dist, q_peak, screen, aquifer, w, limits)
            if reasons:
                tried.append({"distance": dist, "production": n_p, "injection": n_i, "result": ", ".join(reasons)})
                continue
            thermal = _thermal(wells, aquifer, k_aq, c_aq, q_op, spread_month, active, ld.years, t_gw)
            ok = thermal[2] <= limits["drift"]
            tried.append({"distance": dist, "production": n_p, "injection": n_i,
                          "result": "ok" if ok else f"drift {thermal[2]:.2f} K"})
            if ok:
                choice = (n_p, n_i, dist, wells, thermal)
                break
        if choice is None:  # nothing fits: show the largest distance with the most wells tried
            feasible = False
            dist = w["max_distance"]
            n_p, n_i, wells, _ = _fewest_wells(dist, q_peak, screen, aquifer, w, limits)
            thermal = _thermal(wells, aquifer, k_aq, c_aq, q_op, spread_month, active, ld.years, t_gw)
        else:
            n_p, n_i, dist, wells, thermal = choice
    lines, temps, drift, breakthrough, darcy, retardation = thermal

    peak = _hydraulics(wells, aquifer, w)
    if not aquifer["confined"]:  # screen from 2 m below the lowest water level; longer than the first guess
        screen = Screen(min(screen.top, aquifer["water_depth"] + peak.drawdown + 2.0), screen.bottom, screen.depth)
    mean_wells = [Well(x.x, x.y, x.q * q_op / q_peak) for x in wells]
    mean = _hydraulics(mean_wells, aquifer, w)
    head = aquifer["water_depth"] + peak.drawdown + w["losses_m"]
    head_mean = aquifer["water_depth"] + mean.drawdown + w["losses_m"] * (q_op / q_peak) ** 2
    pump_kwh = volumes * RHO_W * G * head_mean / w["pump_efficiency"] / 3.6e6

    heat_net = float((ld.injection - ld.extraction).sum() * 1000 / 8760)
    plumes = {y: plume_length(heat_net, aquifer["thickness"], c_aq, k_aq, darcy, aquifer["alpha_l"],
                              aquifer["alpha_t"], y, limits["plume_limit"])
              for y in sorted({1, 10, ld.years}) if y <= ld.years}

    spf = hp_el = None
    if ld.heating is not None:
        hp_el_month = (ld.heating - ld.extraction) + (ld.injection - ld.cooling)
        hp_el = float(hp_el_month.sum())
        useful = float(ld.heating.sum() + ld.cooling.sum())
        spf = useful / (hp_el + float(pump_kwh.sum())) if hp_el + pump_kwh.sum() > 0 else None
    monthly = pd.DataFrame({"month": np.arange(1, 13), "extraction_kwh": ld.extraction, "injection_kwh": ld.injection,
                            "volume_m3": volumes, "spread_k": spread_month, "pump_kwh": pump_kwh})

    return Design(
        mode=w["mode"], n_production=n_p, n_injection=n_i, distance=dist, wells=wells, screen=screen,
        t_groundwater=t_gw, q_peak=q_peak, q_operating=q_op, volume_year=float(volumes.sum()), peak=peak, mean=mean,
        drawdown_allowed=s_allow, rise_allowed=aquifer["water_depth"] - limits["freeboard"],
        v_entrance_production=entrance_velocity(q_peak / n_p, w["r_bore"], screen.length),
        v_entrance_injection=entrance_velocity(q_peak / n_i, w["r_bore"], screen.length) * w["reserve"],
        v_allowed=aq.sichardt_velocity(aquifer["kf"]), pump_head=head,
        pump_power=pump_power(q_peak, head, w["pump_efficiency"]),
        pump_depth=aquifer["water_depth"] + peak.drawdown + PUMP_SUBMERGENCE, pump_energy_year=float(pump_kwh.sum()),
        darcy=darcy, critical_distance=critical_distance(q_op, aquifer["thickness"], darcy), k_aquifer=k_aq,
        c_aquifer=c_aq, retardation=retardation, streamlines=lines, temperatures=temps, drift=drift,
        breakthrough_years=breakthrough, heat_net_w=heat_net, plume=plumes, monthly=monthly, spf=spf,
        hp_electricity_year=hp_el, tried=tried, loads=ld, feasible=feasible)


def _fewest_wells(dist, q, screen, aquifer, w, limits):
    """Fewest production and injection wells that meet the hydraulic limits at this distance."""
    n_p = n_i = 1
    reasons = []
    for _ in range(2 * MAX_WELLS):
        wells = layout(n_p, n_i, dist, q, w["orientation"], w["spacing"])
        reasons = _hydraulic_ok(_hydraulics(wells, aquifer, w), q, n_p, n_i, screen, aquifer, w, limits)
        if not reasons:
            return n_p, n_i, wells, []
        grow_p = "drawdown" in reasons or "entrance production" in reasons
        grow_i = "rise" in reasons or "entrance injection" in reasons
        if (grow_p and n_p >= MAX_WELLS) or (grow_i and n_i >= MAX_WELLS):
            break
        n_p += grow_p
        n_i += grow_i
    return n_p, n_i, wells, reasons
