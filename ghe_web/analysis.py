"""Post-processing of a calculated borefield: key results, hydraulics, sensitivity, optimisation.

No Streamlit code here, so everything can be tested and reused on its own.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import model, properties
from .properties import SectionInput
from .properties.load import HOURS_PER_MONTH, MONTHS

LAMINAR_RE = 2300
MONTH_END_HOURS = np.cumsum(HOURS_PER_MONTH)  # hour of the year at which each month ends


@dataclass
class KeyResults:
    rows: list[tuple[str, str, str]]  # (label, value, explanation)
    warnings: list[str]
    values: dict[str, float]  # the same numbers, unformatted, for comparisons and reports
    groups: list[str] = field(default_factory=list)  # heading of each row, same length as rows

    def by_group(self) -> dict[str, list[tuple[str, str, str]]]:
        out: dict[str, list[tuple[str, str, str]]] = {}
        for group, row in zip(self.groups, self.rows):
            out.setdefault(group, []).append(row)
        return out


def _when(index: int, per_year: int) -> str:
    year, rest = divmod(index, per_year)
    month = rest if per_year == 12 else int(np.searchsorted(MONTH_END_HOURS, rest, side="right"))
    return f"{MONTHS[month]}, year {year + 1}"


def key_results(result: model.SizingResult, inputs: dict[str, SectionInput]) -> KeyResults:
    bf = result.borefield
    load = bf.load
    limits = inputs["limits"].values
    rows, groups, warns, vals = [], [], [], {}

    def add(group: str, label: str, value: str, note: str = "") -> None:
        groups.append(group)
        rows.append((label, value, note))

    temps = "Temperatures"
    if result.hourly_basis:
        tf = result.hourly_temperatures["Average fluid"].to_numpy()
        tf_min_series = tf_max_series = tf
        per_year = 8760
    else:
        tf_min_series = result.temperatures["Average fluid (peak extraction)"].to_numpy()
        tf_max_series = result.temperatures["Average fluid (peak injection)"].to_numpy()
        per_year = 12
    t_min, t_max = float(tf_min_series.min()), float(tf_max_series.max())
    i_min, i_max = int(tf_min_series.argmin()), int(tf_max_series.argmax())
    vals.update(t_min=t_min, t_max=t_max)
    add(temps, "Lowest average fluid temperature", f"{t_min:.2f} °C",
        f"{_when(i_min, per_year)}; limit {limits['T_min']} °C")
    add(temps, "Highest average fluid temperature", f"{t_max:.2f} °C",
        f"{_when(i_max, per_year)}; limit {limits['T_max']} °C")

    margin_cold = t_min - limits["T_min"]
    margin_warm = limits["T_max"] - t_max
    vals.update(margin_cold=margin_cold, margin_warm=margin_warm)
    if result.sizing_method == "check":
        ok = margin_cold >= -0.05 and margin_warm >= -0.05
        vals["passes"] = float(ok)
        add(temps, "Check against the limits", "passes" if ok else "fails",
            f"{margin_cold:+.2f} K to the minimum, {margin_warm:+.2f} K to the maximum")
        if not ok:
            warns.append("The given borehole length does not keep the fluid within the temperature limits.")
    elif abs(margin_cold - margin_warm) < 0.3:
        add(temps, "Size decided by", "both limits", "heating and cooling need about the same length")
    else:
        limiting = "heating (minimum temperature)" if margin_cold < margin_warm else "cooling (maximum temperature)"
        add(temps, "Size decided by", limiting,
            f"the other limit still has {max(margin_cold, margin_warm):.1f} K margin")

    extremes = yearly_extremes(result)
    if len(extremes) > 1:
        drift = float(extremes["Lowest"].iloc[-1] - extremes["Lowest"].iloc[0])
        vals["drift_k"] = drift
        add(temps, "Long-term drift", f"{drift:+.1f} K",
            f"change of the yearly lowest temperature from year 1 to year {len(extremes)}; "
            "a large drift means the ground is out of balance")

    res = bf.results
    if result.hourly_basis and "Into borefield" in result.hourly_temperatures:
        inlet = result.hourly_temperatures["Into borefield"]
        t_in_min, t_in_max = float(inlet.min()), float(inlet.max())
    elif not bf.borehole.use_constant_Rb and len(model._optional(res, "peak_extraction_inlet")):
        t_in_min = float(np.min(res.peak_extraction_inlet))
        t_in_max = float(np.max(res.peak_injection_inlet))
    else:
        t_in_min = t_in_max = None
    if t_in_min is not None:
        vals.update(t_inlet_min=t_in_min, t_inlet_max=t_in_max)
        add(temps, "Coldest fluid into the borefield", f"{t_in_min:.2f} °C",
            "supply from the heat pump at peak heating")
        add(temps, "Warmest fluid into the borefield", f"{t_in_max:.2f} °C", "at peak cooling")
        freezing = getattr(bf.borehole.fluid_data, "freezing_point", None)
        if isinstance(freezing, (int, float)) and t_in_min < freezing + 3:
            warns.append(f"The coldest fluid ({t_in_min:.1f} °C) is close to the freezing point of the fluid "
                         f"({freezing:.1f} °C). Use more antifreeze or a higher minimum temperature.")

    energy = "Ground energy"
    extraction = float(np.sum(load.monthly_baseload_extraction)) / 1000
    injection = float(np.sum(load.monthly_baseload_injection)) / 1000
    imbalance = injection - extraction
    vals.update(extraction_mwh=extraction, injection_mwh=injection, imbalance_mwh=imbalance)
    add(energy, "Ground energy per year", f"{extraction:,.0f} MWh out, {injection:,.0f} MWh in",
        "after heat pump efficiency" if hasattr(load, "yearly_electricity_consumption_heating") else
        "as entered (ground side)")
    add(energy, "Yearly imbalance", f"{imbalance:+,.0f} MWh",
        "positive: the ground warms up over the years; negative: it cools down")

    total = result.total_length
    peak_ext = float(load.max_peak_extraction)
    peak_inj = float(load.max_peak_injection)
    vals.update(w_per_m_extraction=peak_ext * 1000 / total, w_per_m_injection=peak_inj * 1000 / total,
                kwh_per_m=extraction * 1000 / total)
    add(energy, "Specific extraction", f"{peak_ext * 1000 / total:.1f} W/m peak, "
        f"{extraction * 1000 / total:.0f} kWh/m per year", "VDI 4640 rule of thumb: 30 to 60 W/m")
    add(energy, "Specific injection", f"{peak_inj * 1000 / total:.1f} W/m peak")
    if peak_ext > 0:
        flh = extraction * 1000 / peak_ext
        vals["full_load_hours"] = flh
        add(energy, "Full-load hours, heating" + (" and hot water" if _has_dhw(load) else ""),
            f"{flh:,.0f} h per year", "VDI 4640 W/m values assume 1800 h (heating only) or 2400 h (with hot water)")

    hyd_group = "Borehole and hydraulics"
    add(hyd_group, "Borehole thermal resistance", f"{result.borehole_resistance:.3f} m·K/W",
        "measured value" if bf.borehole.use_constant_Rb else "calculated from pipe, grout and flow")
    vals["Rb"] = result.borehole_resistance
    if result.reynolds is not None:
        re = result.reynolds
        vals["Re"] = re
        regime = "laminar" if re < LAMINAR_RE else "transitional" if re < 4000 else "turbulent"
        add(hyd_group, "Reynolds number", f"{re:,.0f} ({regime})",
            "at the coldest fluid; turbulent flow (above ~4000) transfers heat better")
        if re < LAMINAR_RE:
            warns.append(f"The flow is laminar (Re = {re:,.0f}). A higher flow rate, smaller pipes or less antifreeze "
                         "lower the borehole resistance and can shorten the boreholes.")
        hyd = hydraulics(result, inputs, temperature=t_min)
        if hyd:
            vals.update(hyd)
            add(hyd_group, "Pressure drop per borehole", f"{hyd['dp_kpa']:.1f} kPa",
                "at the coldest fluid (highest viscosity); probe only, without manifold and header pipes")
            add(hyd_group, "Pump power", f"{hyd['pump_electric_w']:,.0f} W electrical",
                f"{hyd['pump_w']:,.0f} W hydraulic for the whole field, at {hyd['pump_efficiency']:.0%} pump efficiency")
            add(hyd_group, "Pump energy per year", f"{hyd['pump_mwh']:,.1f} MWh",
                f"at {hyd['pump_hours']:,.0f} running hours; probe pressure drop only")

    hp = result.heat_pump
    if hp is not None:
        group = "Heat pump"
        curve = _cop_curve(bf.load)
        spf = hp["SPF heating"].dropna()
        if len(spf):
            vals.update(spf_heating=float(spf.mean()), spf_first=float(spf.iloc[0]), spf_last=float(spf.iloc[-1]))
            note = (f"year 1: {spf.iloc[0]:.2f}, year {len(spf)}: {spf.iloc[-1]:.2f}; heating demand per kWh of "
                    "electricity" if curve else "fixed value from the inputs")
            add(group, "Seasonal performance factor, heating", f"{spf.mean():.2f}", note)
        seer = hp["SEER"].dropna()
        if len(seer):
            vals["seer"] = float(seer.mean())
            add(group, "Seasonal EER, cooling", f"{seer.mean():.1f}")
        if curve is not None:
            cop_cold = float(np.atleast_1d(curve.get_COP(t_min))[0])
            vals["cop_coldest"] = cop_cold
            add(group, "COP at the coldest fluid", f"{cop_cold:.2f}", f"at {t_min:.1f} °C average fluid temperature")
        elec = hp[["Electricity heating [MWh]", "Electricity cooling [MWh]", "Electricity hot water [MWh]"]]
        total = float(elec.sum(axis=1).mean())
        vals["electricity_mwh"] = total
        short = {"Electricity heating [MWh]": "heating", "Electricity cooling [MWh]": "cooling",
                 "Electricity hot water [MWh]": "hot water"}
        parts = ", ".join(f"{short[name]} {elec[name].mean():,.1f}" for name in elec if elec[name].mean() > 0)
        add(group, "Heat pump electricity per year", f"{total:,.1f} MWh", parts + " MWh (average over the years)")

    return KeyResults(rows, warns, vals, groups)


def _has_dhw(load) -> bool:
    dhw = getattr(load, "monthly_baseload_dhw", None)
    return dhw is not None and float(np.sum(dhw)) > 0


def _cop_curve(load):
    """The load's COP object when it depends on temperature, else None."""
    from GHEtool.VariableClasses.Efficiency import COP
    cop = getattr(load, "cop", None)
    return cop if isinstance(cop, COP) else None


def _pressure_drop(result: model.SizingResult):
    """GHEtool's pressure drop model for one borehole (no header pipes), or None for a measured Rb."""
    from GHEtool.VariableClasses.PipeData.PressureDrop import PressureDrop
    bf = result.borefield
    if bf.borehole.use_constant_Rb:
        return None
    return PressureDrop(bf.borehole.pipe_data, bf.borehole.fluid_data, bf.borehole.flow_data,
                        minor_losses_borehole=0, borehole_length=result.borehole_length,
                        r_in_lateral=0.02, distance_lateral=0, minor_losses_lateral=0,
                        r_in_main=0.05, distance_main=0, minor_losses_main=0,
                        nb_of_boreholes=result.number_of_boreholes, series_factor=1, tichelmann_factor=1)


def hydraulics(result: model.SizingResult, inputs: dict[str, SectionInput],
               temperature: float | None = None) -> dict[str, float] | None:
    """Pressure drop in one borehole and the hydraulic power to pump the whole field.

    Evaluated at the given fluid temperature (default: the mean base-load temperature)."""
    bf = result.borefield
    drop = _pressure_drop(result)
    if drop is None:
        return None
    try:
        if temperature is None:
            temperature = float(np.mean(result.temperatures["Average fluid (base load)"]))
        dp_kpa = float(drop.calculate_pressure_drop_borehole(temperature=temperature))
        rho = float(bf.borehole.fluid_data.rho(temperature=temperature))
        mfr = float(bf.borehole.flow_data.mfr_borehole(fluid_data=bf.borehole.fluid_data, temperature=temperature))
    except Exception:  # not every pipe/flow combination supports this; the rest of the results still stand
        return None
    flow_m3s = mfr / rho * result.number_of_boreholes
    pump_w = dp_kpa * 1000 * flow_m3s
    flow = inputs["flow"].values
    efficiency = flow.get("pump_efficiency", 35.0) / 100
    hours = flow.get("pump_hours", 4000.0)
    return {"dp_kpa": dp_kpa, "pump_w": pump_w, "pump_efficiency": efficiency, "pump_electric_w": pump_w / efficiency,
            "pump_hours": hours, "pump_mwh": pump_w / efficiency * hours / 1e6}


# ---------------------------------------------------------------- tables for graphs

def yearly_extremes(result: model.SizingResult) -> pd.DataFrame:
    """Lowest and highest average fluid temperature of every simulated year."""
    if result.hourly_basis:
        tf = result.hourly_temperatures["Average fluid"].to_numpy()
        years = tf.reshape(-1, 8760)
        low, high = years.min(axis=1), years.max(axis=1)
    else:
        t = result.temperatures
        low = t["Average fluid (peak extraction)"].to_numpy().reshape(-1, 12).min(axis=1)
        high = t["Average fluid (peak injection)"].to_numpy().reshape(-1, 12).max(axis=1)
    return pd.DataFrame({"Year": range(1, len(low) + 1), "Lowest": low, "Highest": high})


def monthly_ground_energy(result: model.SizingResult) -> pd.DataFrame:
    load = result.borefield.load
    return pd.DataFrame({"Month": MONTHS,
                         "Extraction": np.asarray(load.monthly_baseload_extraction, dtype=float) / 1000,
                         "Injection": np.asarray(load.monthly_baseload_injection, dtype=float) / 1000})


def gfunction_curve(result: model.SizingResult) -> pd.DataFrame:
    bf = result.borefield
    years = bf.load.simulation_period
    seconds = np.logspace(np.log10(3600), np.log10(years * 8760 * 3600), 60)
    g = bf.gfunction(seconds, result.borehole_length)
    ts = result.borehole_length ** 2 / (9 * bf.ground_data.alpha())
    return pd.DataFrame({"ln_t_ts": np.log(seconds / ts), "g": np.asarray(g, dtype=float),
                         "hours": seconds / 3600})


# ---------------------------------------------------------------- sensitivity

def _scaled_load(values: dict, factor: float, variant) -> dict:
    out = dict(values)
    for p in variant.properties:
        if p.kind == "monthly":
            out[p.key] = tuple(x * factor for x in values[p.key])
        elif p.kind == "hourly":
            out[p.key] = {k: [x * factor for x in v] for k, v in values[p.key].items()}
        elif p.scales_with_load:
            out[p.key] = values[p.key] * factor
    return out


def sensitivity(inputs: dict[str, SectionInput]) -> pd.DataFrame:
    """Borehole length when one input changes, the others fixed. Uses monthly sizing for speed."""
    base_inputs = copy.deepcopy(inputs)
    if "hourly_sizing" in base_inputs["load"].values:
        base_inputs["load"].values["hourly_sizing"] = False
    if "calculation" in base_inputs:
        base_inputs["calculation"].variant = "size"
    base = model.size(base_inputs).borehole_length

    cases = [
        ("Ground conductivity ±15 %", "ground", "k_s", 0.85, 1.15),
        ("Ground temperature ±1 K", "ground", "T_g", -1.0, 1.0),
        ("Building load ±10 %", "load", None, 0.9, 1.1),
    ]
    if "k_g" in base_inputs["pipe"].values:
        cases.append(("Grout conductivity ±25 %", "pipe", "k_g", 0.75, 1.25))
    if "Rb" in base_inputs["pipe"].values:
        cases.append(("Borehole resistance ±15 %", "pipe", "Rb", 0.85, 1.15))

    rows = []
    for label, section, key, low, high in cases:
        lengths = []
        for change in (low, high):
            trial = copy.deepcopy(base_inputs)
            values = trial[section].values
            if section == "load":
                variant = properties.get("load").variant(trial["load"].variant)
                trial["load"].values = _scaled_load(values, change, variant)
            elif key == "T_g":
                values[key] = values[key] + change
            else:
                values[key] = values[key] * change
            try:
                lengths.append(model.size(trial).borehole_length)
            except Exception:
                lengths.append(float("nan"))
        rows.append({"Input": label, "Low": lengths[0], "High": lengths[1], "Base": base})
    df = pd.DataFrame(rows)
    df["Spread"] = (df["High"] - df["Low"]).abs()
    return df.sort_values("Spread", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- optimisation

def optimise_layout(inputs: dict[str, SectionInput], length_max: float, width_max: float, spacing_min: float,
                    spacing_max: float, depth_min: float, depth_max: float, trials: int = 60) -> pd.DataFrame:
    """Search rectangular, L, U, box and staggered fields that fit in the plot (GHEtool + optuna)."""
    from GHEtool.Methods import optimise_borefield_configuration
    bf = model.build_borefield(inputs)
    solutions = optimise_borefield_configuration(
        bf, l_1_max=length_max, l_2_max=width_max, b_min=spacing_min, b_max=spacing_max, b_step=0.5,
        h_min=depth_min, h_max=depth_max, nb_of_trials=trials, size_L3=True)
    names = {0: "L-shape", 1: "U-shape", 2: "Box", 3: "Rectangle", 4: "Staggered"}
    rows = []
    for total, params, n, _ in solutions[:10]:
        n_1, n_2, b_1 = params["n_1"], params["n_2"], params["b_1"]
        b_2 = params.get("b_2", b_1)
        shape = params.get("type", params.get("shape"))
        row = {"Layout": names.get(shape, str(shape)), "Boreholes": int(n), "Grid": f"{n_1} × {n_2}",
               "Spacing [m]": f"{b_1} × {b_2}", "Length each [m]": total / n, "Total length [m]": total}
        rows.append(row)
    return pd.DataFrame(rows)


OBJECTIVES = {
    "power": "Most geothermal power",
    "energy": "Most geothermal energy",
    "balance": "Balanced ground",
}


def _hourly_period(load, name: str) -> np.ndarray:
    """Hourly values over the whole simulation period, for single-year and multi-year loads alike."""
    arr = getattr(load, f"hourly_{name}_load_simulation_period", None)
    if arr is None:
        arr = np.tile(getattr(load, f"hourly_{name}_load"), load.simulation_period)
    return np.asarray(arr, dtype=float)


def load_optimisation(result: model.SizingResult, objective: str = "power") -> dict | None:
    """Keeps the borefield as designed and splits the hourly building demand into the part the ground can take
    within the temperature limits and the rest for a boiler or chiller (GHEtool's load optimisation).

    power: the largest constant share of the peaks; energy: the most energy, month by month;
    balance: the most power while keeping the ground in balance over the years."""
    from GHEtool import HourlyBuildingLoad
    from GHEtool.Methods import (optimise_load_profile_balance, optimise_load_profile_energy,
                                 optimise_load_profile_power)
    from GHEtool.VariableClasses import HourlyBuildingLoadMultiYear
    load = result.borefield.load
    if not isinstance(load, (HourlyBuildingLoad, HourlyBuildingLoadMultiYear)):
        return None
    bf = copy.deepcopy(result.borefield)
    if objective == "power":
        ground, external = optimise_load_profile_power(bf, load, use_hourly_resolution=False)
    elif objective == "energy":
        ground, external = optimise_load_profile_energy(bf, load)
    elif objective == "balance":
        ground, external = optimise_load_profile_balance(bf, load, use_hourly_resolution=False)
    else:
        raise ValueError(f"Unknown objective {objective!r}")

    years = load.simulation_period
    series = {}
    for who, obj in (("Building", load), ("Ground", ground), ("External", external)):
        for kind in ("heating", "cooling"):
            series[f"{who} {kind}"] = _hourly_period(obj, kind)
    hours = np.concatenate(([0], MONTH_END_HOURS))

    def monthly(arr):  # average year, MWh per month
        per_year = arr.reshape(years, 8760)
        return np.array([per_year[:, a:b].sum() for a, b in zip(hours[:-1], hours[1:])]) / years / 1000

    month_table = pd.DataFrame({"Month": MONTHS} | {f"{k} [MWh]": monthly(v) for k, v in series.items()})
    yearly = pd.DataFrame({"Year": np.arange(1, years + 1)} | {
        f"{k} [MWh]": v.reshape(years, 8760).sum(axis=1) / 1000 for k, v in series.items()})
    first_year = pd.DataFrame({f"{k} [kW]": v[:8760] for k, v in series.items()},
                              index=pd.RangeIndex(1, 8761, name="Hour"))

    def share(kind):
        total = series[f"Building {kind}"].sum()
        return float(series[f"Ground {kind}"].sum() / total) if total else 1.0

    return {
        "objective": objective,
        "heating_share": share("heating"), "cooling_share": share("cooling"),
        "ground_peak_heating_kw": float(series["Ground heating"].max()),
        "ground_peak_cooling_kw": float(series["Ground cooling"].max()),
        "backup_heating_kw": float(series["External heating"].max()),
        "backup_cooling_kw": float(series["External cooling"].max()),
        "backup_heating_mwh": float(series["External heating"].sum() / years / 1000),
        "backup_cooling_mwh": float(series["External cooling"].sum() / years / 1000),
        "monthly": month_table, "yearly": yearly, "first_year": first_year,
    }


def load_duration(result: model.SizingResult) -> pd.DataFrame | None:
    """Hourly building and ground loads of the first year, each sorted from high to low."""
    load = result.borefield.load
    if not hasattr(load, "hourly_heating_load"):
        return None
    out = {"Hours": np.arange(1, 8761)}
    out["Heating demand"] = np.sort(np.asarray(load.hourly_heating_load, dtype=float))[::-1]
    out["Cooling demand"] = np.sort(np.asarray(load.hourly_cooling_load, dtype=float))[::-1]
    for name in ("extraction", "injection"):
        arr = getattr(load, f"hourly_{name}_load_simulation_period", None)
        if arr is not None:
            out[f"Ground {name}"] = np.sort(np.asarray(arr, dtype=float)[:8760])[::-1]
    return pd.DataFrame(out)


def pressure_drop_curve(result: model.SizingResult, temperature: float) -> pd.DataFrame | None:
    """Pressure drop over one borehole for flow rates from zero to twice the design flow."""
    drop = _pressure_drop(result)
    if drop is None:
        return None
    try:
        dp, _, _, flows = drop.create_pressure_drop_curve(range=2, datapoints=40, temperature=temperature)
    except Exception:
        return None
    return pd.DataFrame({"Flow per borehole [l/s]": flows, "Pressure drop [kPa]": dp})[1:]


def ground_temperature_map(result: model.SizingResult, cells: int = 90) -> dict | None:
    """Ground temperature around the field at mid-depth at the end of the simulation, caused by the yearly
    imbalance (finite line source with mirror image, superposed over all boreholes).

    Shows how far the field changes the ground and how the boreholes influence each other. Seasonal swings
    are left out: they average out over a year."""
    from scipy.special import erfc
    bf = result.borefield
    holes = bf.borefield
    xs = np.array([b.x for b in holes])
    ys = np.array([b.y for b in holes])
    H, D, r_b = holes[0].H, holes[0].D, holes[0].r_b
    years = bf.load.simulation_period
    t = years * 8760 * 3600.0
    k = float(bf.ground_data.k_s(H + D, D))
    alpha = float(bf.ground_data.alpha(H + D, D))
    t_ground = float(bf.ground_data.calculate_Tg(H + D, D))
    load = bf.load
    imbalance_w = (float(np.sum(load.monthly_baseload_injection)) - float(np.sum(load.monthly_baseload_extraction))
                   ) * 1000 / 8760  # kWh per year to W
    q = imbalance_w / result.total_length  # W/m, positive warms the ground

    # temperature change around one borehole as a function of distance, then superposed
    z = D + H / 2
    zs = np.linspace(D, D + H, 2001)
    radii = np.geomspace(r_b, 2000.0, 400)
    d1 = np.sqrt(radii[:, None] ** 2 + (z - zs[None, :]) ** 2)
    d2 = np.sqrt(radii[:, None] ** 2 + (z + zs[None, :]) ** 2)
    integrand = erfc(d1 / (2 * np.sqrt(alpha * t))) / d1 - erfc(d2 / (2 * np.sqrt(alpha * t))) / d2
    unit = np.trapezoid(integrand, zs, axis=1) / (4 * np.pi * k)  # K per W/m

    span = max(xs.max() - xs.min(), ys.max() - ys.min(), H / 2)
    margin = max(span * 0.6, 20.0)
    gx = np.linspace(xs.min() - margin, xs.max() + margin, cells)
    gy = np.linspace(ys.min() - margin, ys.max() + margin, cells)
    X, Y = np.meshgrid(gx, gy)
    dT = np.zeros_like(X)
    for x0, y0 in zip(xs, ys):
        r = np.maximum(np.hypot(X - x0, Y - y0), r_b)
        dT += np.interp(np.log(r), np.log(radii), unit)
    dT *= q
    table = pd.DataFrame({"x": X.ravel(), "y": Y.ravel(), "Change": dT.ravel(), "Temperature": t_ground + dT.ravel()})
    return {"table": table, "boreholes": pd.DataFrame({"x": xs, "y": ys}), "q_w_per_m": q,
            "t_ground": t_ground, "depth": z, "years": years, "max_change": float(np.abs(dT).max()),
            "cell": float(gx[1] - gx[0])}
