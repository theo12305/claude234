"""Charts for inputs and results. No Streamlit code here, so they can be tested on their own.

Input charts are looked up per (section, variant) in DRAWINGS, so a new variant
(e.g. a coaxial pipe) only needs a new entry to get its own picture.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Callable

import altair as alt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from . import i18n  # noqa: E402
from .i18n import fmt, t  # noqa: E402
from .properties import SectionInput  # noqa: E402
from .properties.load import MONTHS  # noqa: E402

alt.data_transformers.disable_max_rows()  # hourly charts have more than Altair's default 5000 rows

GROUT = "#c9c4b8"
GROUND = "#e8e2d0"
PIPE_DOWN = "#d1495b"  # supply
PIPE_UP = "#2e86ab"  # return
# Building demand: heating red, cooling blue. Energy in the ground: extraction blue (it cools the ground), injection
# red (it warms the ground), the same colours as the cold and warm fluid in the temperature charts.
HEATING = PIPE_DOWN
COOLING = PIPE_UP
EXTRACTION = PIPE_UP
INJECTION = PIPE_DOWN
NEUTRAL = "#8a8f98"  # labels and markers on charts, readable on light and dark pages


def _load_colors(heating: str, cooling: str) -> alt.Scale:
    return alt.Scale(domain=[heating, cooling], range=[HEATING, COOLING])


def _months() -> list[str]:
    """Month names in the current language, in calendar order (for sorting chart axes)."""
    return list(i18n.months())


def _month_names(values) -> list[str]:
    """English month abbreviations (as in the result tables) in the current language."""
    names = dict(zip(MONTHS, i18n.months()))
    return [names.get(v, v) for v in values]


# ---------------------------------------------------------------- inputs

def rectangular_layout(values: dict) -> plt.Figure:
    xs = [i * values["B_1"] for i in range(values["N_1"]) for _ in range(values["N_2"])]
    ys = [j * values["B_2"] for _ in range(values["N_1"]) for j in range(values["N_2"])]
    return borefield_layout(xs, ys, t("{n} boreholes, {b1:g} m × {b2:g} m spacing", n=len(xs), b1=values["B_1"],
                                      b2=values["B_2"]))


def custom_layout(values: dict) -> plt.Figure:
    from .geometry import closest_pair
    xs = [p[0] for p in values["points"]]
    ys = [p[1] for p in values["points"]]
    pair = closest_pair(values["points"])
    title = t("{n} boreholes, closest {d:.1f} m apart", n=len(xs), d=pair[0]) if pair else \
        t("{n} boreholes", n=len(xs))
    return borefield_layout(xs, ys, title, numbered=len(xs) <= 150)


def borefield_layout(xs: list, ys: list, title: str, numbered: bool = False) -> plt.Figure:
    """Top view of the borefield."""
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(xs, ys, s=40, color=PIPE_UP, zorder=3)
    if numbered:
        for n, (x, y) in enumerate(zip(xs, ys), start=1):
            ax.annotate(str(n), (x, y), textcoords="offset points", xytext=(4, 4), fontsize=6, color="#555")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.3)
    ax.margins(0.08)
    fig.tight_layout()
    return fig


def _coaxial_cross_section(values: dict, r_b_mm: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.add_patch(Circle((0, 0), r_b_mm * 1.6, color=GROUND))
    ax.add_patch(Circle((0, 0), r_b_mm, facecolor=GROUT, edgecolor="#555"))
    ax.add_patch(Circle((0, 0), values["r_out_out_mm"], color="#888"))
    ax.add_patch(Circle((0, 0), values["r_out_in_mm"], color=PIPE_UP))
    ax.add_patch(Circle((0, 0), values["r_in_out_mm"], color="#888"))
    ax.add_patch(Circle((0, 0), values["r_in_in_mm"], color=PIPE_DOWN))
    lim = r_b_mm * 1.6
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(t("Borehole Ø {d:.0f} mm, outer pipe Ø {p:.0f} mm", d=2 * r_b_mm, p=2 * values["r_out_out_mm"]),
                 fontsize=10)
    ax.legend(handles=[Circle((0, 0), 1, color=PIPE_DOWN, label=t("Fluid going down (inner pipe)")),
                       Circle((0, 0), 1, color=PIPE_UP, label=t("Fluid going up (annulus)"))],
              loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    return fig


def _u_tube_cross_section(values: dict, r_b_mm: float, legs: int) -> plt.Figure:
    """Borehole seen from above with its U-tube legs. ``legs`` = 2 (single U) or 4 (double U)."""
    d = values["D_s_mm"]
    positions = [(-d, 0), (d, 0)] if legs == 2 else [(-d, 0), (0, -d), (d, 0), (0, d)]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.add_patch(Circle((0, 0), r_b_mm * 1.6, color=GROUND))
    ax.add_patch(Circle((0, 0), r_b_mm, facecolor=GROUT, edgecolor="#555"))
    for i, (x, y) in enumerate(positions):
        color = PIPE_DOWN if i < legs // 2 else PIPE_UP
        ax.add_patch(Circle((x, y), values["r_out_mm"], color=color))
        ax.add_patch(Circle((x, y), values["r_in_mm"], color="white"))
    ax.set_xlim(-r_b_mm * 1.6, r_b_mm * 1.6)
    ax.set_ylim(-r_b_mm * 1.6, r_b_mm * 1.6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(t("Borehole Ø {d:.0f} mm, pipe Ø {p:.0f} mm", d=2 * r_b_mm, p=2 * values["r_out_mm"]), fontsize=10)
    ax.legend(handles=[Circle((0, 0), 1, color=PIPE_DOWN, label=t("Fluid going down")),
                       Circle((0, 0), 1, color=PIPE_UP, label=t("Fluid going up"))],
              loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    return fig


def ground_rows(inputs: dict[str, SectionInput]) -> tuple[list[dict], bool]:
    """The layer table of the ground section, or one uniform layer from the single conductivity.
    The flag is True when the calculation uses the layers."""
    from .properties.ground import layered
    v = inputs["ground"].values
    rows = list((v.get("layers") or {}).get("rows") or ())
    if rows:
        return rows, layered(v)
    depth = _drawn_depth(inputs)[0] + _drawn_depth(inputs)[1]
    return [{"top": 0.0, "bottom": max(depth, 1.0), "rock": "Uniform ground", "k_s": v["k_s"],
             "C": v["volumetric_heat_capacity"]}], False


def borehole_log(rows: list[dict], length: float, buried: float = 0.0, title: str = "",
                 groundwater: float | None = None, size: tuple[float, float] = (6.2, 6.4)) -> plt.Figure:
    """A borehole log: the layers with rock colours and hatching, the borehole, and the conductivity with depth
    next to it (dashed: the average over the borehole, which is what a single-value calculation uses)."""
    from .strata import predict, rocks
    end = buried + length
    deepest = max(end, float(rows[-1]["top"]) + 2) * 1.12  # the last layer continues downwards
    plt.rcParams["hatch.linewidth"] = 0.5
    fig, (ax, axk) = plt.subplots(1, 2, figsize=size, sharey=True, gridspec_kw={"width_ratios": [1.5, 1]})
    for i, r in enumerate(rows):
        top = float(r["top"])
        bottom = float(r["bottom"]) if i < len(rows) - 1 else deepest
        rock = r.get("rock", "")
        name = t(rock) + (t(", moist") if "above groundwater" in (r.get("basis") or "") else "")
        bottom = min(bottom, deepest)
        if bottom <= top:
            continue
        ax.add_patch(plt.Rectangle((0, top), 1, bottom - top, facecolor=rocks.color(rock), hatch=rocks.hatch(rock),
                                   edgecolor="#00000055", linewidth=0.5))
        if bottom - top > deepest * 0.025:
            label = name + fmt("\n{k:.1f} W/(m·K)", k=float(r["k_s"])) if bottom - top > deepest * 0.06 else name
            ax.text(1.06, (top + bottom) / 2, label, va="center", fontsize=7.5, clip_on=False)
        axk.plot([float(r["k_s"])] * 2, [top, bottom], color="#2e86ab", linewidth=2)
        if i:
            axk.plot([float(rows[i - 1]["k_s"]), float(r["k_s"])], [top, top], color="#2e86ab", linewidth=1)
    # the borehole
    ax.add_patch(plt.Rectangle((0.42, buried), 0.16, length, facecolor="white", edgecolor="black", linewidth=1.2,
                               zorder=3))
    ax.plot([0.47, 0.47], [buried, end - 0.5], color=PIPE_DOWN, linewidth=1.4, zorder=4)
    ax.plot([0.53, 0.53], [buried, end - 0.5], color=PIPE_UP, linewidth=1.4, zorder=4)
    ax.annotate(fmt("{x:.0f} m", x=length), (0.5, end), xytext=(0, -3), textcoords="offset points", ha="center", va="top",
                fontsize=8, weight="bold", zorder=5, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    if groundwater is not None and groundwater < deepest:
        ax.plot([0, 1], [groundwater] * 2, color="#1565c0", linewidth=1.5, zorder=2)
        ax.text(-0.04, groundwater, t("GW ▽"), fontsize=7, color="#1565c0", va="center", ha="right")
    k_avg, _ = predict.effective(rows, length, buried)
    axk.axvline(k_avg, color="#d1495b", linestyle="--", linewidth=1.2)
    axk.text(k_avg, deepest * 0.01, t(" average {k:.2f}", k=k_avg), color="#d1495b", fontsize=7.5, va="top")
    axk.axhspan(buried, end, color="#f2f2f2", zorder=0)
    ax.set_xlim(-0.1, 1)
    ax.set_ylim(deepest, 0)
    ax.set_xticks([])
    ax.set_ylabel(t("Depth below ground [m]"))
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ks = [float(r["k_s"]) for r in rows]
    axk.set_xlim(0, max(ks + [k_avg]) * 1.25)
    axk.set_xlabel(t("Thermal conductivity [W/(m·K)]"))
    axk.grid(alpha=0.3)
    ax.set_title(title or t("Ground layers"), fontsize=10, loc="left")
    fig.tight_layout()
    fig.subplots_adjust(wspace=0.75)
    return fig


def _drawn_depth(inputs: dict[str, SectionInput]) -> tuple[float, float]:
    """Length and buried depth of what is drawn in the ground: the boreholes, or the wells down to the aquifer
    bottom."""
    if inputs.get("system") is not None and inputs["system"].variant == "open" and "aquifer" in inputs:
        return float(inputs["aquifer"].values["bottom"]), 0.0
    bf = inputs["borefield"].values
    return bf["H"], bf["D"]


def ground_log_drawing(inputs: dict[str, SectionInput]) -> plt.Figure:
    rows, used = ground_rows(inputs)
    title = t("Ground layers") if used else (t("Ground layers (not used: switch on the layered calculation)")
                                             if rows[0].get("rock") != "Uniform ground" else t("Uniform ground"))
    return borehole_log(rows, *_drawn_depth(inputs), title, size=(6.4, 3.6))  # compact next to the ground fields


def conductivity_with_length(rows: list[dict], buried: float, lengths, sized: float | None = None) -> alt.Chart:
    """Average conductivity over the borehole for each borehole length: why a deeper borehole may gain more
    (or less) per metre."""
    from .strata import predict
    df = pd.DataFrame({"Borehole length": list(lengths)})
    df["Average conductivity"] = [predict.effective(rows, float(h), buried)[0] for h in df["Borehole length"]]
    line = alt.Chart(df).mark_line(color="#2e86ab").encode(
        x=alt.X("Borehole length:Q", title=t("Borehole length [m]")),
        y=alt.Y("Average conductivity:Q", title=t("Average conductivity [W/(m·K)]"), scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("Borehole length:Q", format=".0f", title=t("Borehole length")),
                 alt.Tooltip("Average conductivity:Q", format=".2f", title=t("Average conductivity"))])
    if sized is None:
        return line.properties(height=260)
    rule = alt.Chart(pd.DataFrame({"x": [sized]})).mark_rule(color="#d1495b", strokeDash=[5, 3]).encode(x="x:Q")
    return (line + rule).properties(height=260)


def layer_share_chart(parts: list[dict]) -> alt.Chart:
    """Per layer along the borehole: its length and its share of the heat exchange (length × conductivity)."""
    from .strata import rocks
    df = pd.DataFrame([{"Layer": fmt("{top:g}–{bottom:.4g} m ", top=float(p["top"]), bottom=float(p["bottom_shown"]))
                        + t(p["rock"]) + (t(" (moist)") if "above groundwater" in (p.get("basis") or "") else ""),
                        "Rock": p["rock"],
                        "Share": p["share"], "Length": p["length"], "Conductivity": float(p["k_s"]),
                        "order": i} for i, p in enumerate(parts)])
    names = list(dict.fromkeys(df["Rock"]))
    return alt.Chart(df).mark_bar().encode(
        y=alt.Y("Layer:N", sort=alt.EncodingSortField("order"), title=None),
        x=alt.X("Share:Q", axis=alt.Axis(format="%"), title=t("Share of the heat exchange")),
        color=alt.Color("Rock:N", scale=alt.Scale(domain=names, range=[rocks.color(n) for n in names]),
                        legend=None),
        stroke=alt.value("#444"), strokeWidth=alt.value(0.5),
        tooltip=[alt.Tooltip("Layer:N", title=t("Layer")),
                 alt.Tooltip("Length:Q", format=".1f", title=t("Length in the layer [m]")),
                 alt.Tooltip("Conductivity:Q", format=".2f", title=t("Thermal conductivity [W/(m·K)]")),
                 alt.Tooltip("Share:Q", format=".0%", title=t("Share"))],
    ).properties(height=max(120, 34 * len(df)))


def load_profile(values: dict) -> alt.Chart:
    """Monthly extracted and injected energy as bars."""
    ext, inj = t("Extraction (heating, cools the ground)"), t("Injection (cooling, warms the ground)")
    data = pd.DataFrame({
        "Month": _months() * 2,
        "Energy": [-float(x) for x in values["baseload_extraction"]]
                  + [float(x) for x in values["baseload_injection"]],
        "Type": [ext] * 12 + [inj] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=_months(), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title=t("Energy [kWh] (extraction below zero)")),
        color=alt.Color("Type:N", scale=alt.Scale(domain=[ext, inj], range=[EXTRACTION, INJECTION]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Type:N", title=t("Load")),
                 alt.Tooltip("Energy:Q", format=",.0f", title="kWh")],
    ).properties(height=300, title=t("Monthly ground load"))


def annual_demand_chart(values: dict) -> alt.Chart:
    from .properties.load import _annual_to_monthly
    heat, cool, heat_peak, cool_peak = _annual_to_monthly(values)
    heating, cooling = t("Heating demand"), t("Cooling demand")
    data = pd.DataFrame({
        "Month": _months() * 2,
        "Energy": [h / 1000 for h in heat] + [-c / 1000 for c in cool],
        "Peak": heat_peak + [-c for c in cool_peak],
        "Type": [heating] * 12 + [cooling] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=_months(), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title=t("Building demand [MWh]")),
        color=alt.Color("Type:N", scale=_load_colors(heating, cooling), legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Type:N", title=t("Load")),
                 alt.Tooltip("Energy:Q", format=",.1f", title="MWh"),
                 alt.Tooltip("Peak:Q", format=",.0f", title=t("Peak kW"))],
    ).properties(height=280, title=t("Building demand per month (before heat pump efficiency)"))


def hourly_demand(values: dict) -> tuple[alt.Chart, alt.Chart]:
    """Daily peak demand over the year next to the load duration curve."""
    prof = values["profile"]
    heating, cooling = t("Heating"), t("Cooling")
    hourly = pd.DataFrame({heating: prof["heating"], cooling: prof["cooling"]})
    daily = hourly.groupby(hourly.index // 24).max()
    daily.index = pd.Index(range(1, len(daily) + 1), name="Day")
    data = daily.reset_index().melt("Day", var_name="Type", value_name="Power")
    colors = _load_colors(heating, cooling)
    over_year = alt.Chart(data).mark_line(strokeWidth=1).encode(
        x=alt.X("Day:Q", title=t("Day of the year"), scale=alt.Scale(domain=[1, 365])),
        y=alt.Y("Power:Q", title=t("Daily peak demand [kW]")),
        color=alt.Color("Type:N", scale=colors, legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Day:Q", title=t("Day")), alt.Tooltip("Type:N", title=t("Load")),
                 alt.Tooltip("Power:Q", format=".1f", title="kW")],
    ).properties(height=260, title=t("Daily peak demand"))
    # Load duration curve: hours sorted from highest to lowest demand (every 10th hour is enough to draw it)
    duration = pd.concat([
        pd.DataFrame({"Hours": range(1, len(hourly) + 1), "Power": sorted(hourly[c], reverse=True), "Type": c})
        .iloc[::10] for c in (heating, cooling)])
    curve = alt.Chart(duration).mark_line().encode(
        x=alt.X("Hours:Q", title=t("Hours per year"), scale=alt.Scale(domain=[0, 8760])),
        y=alt.Y("Power:Q", title=t("Demand [kW]")),
        color=alt.Color("Type:N", scale=colors, legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Type:N", title=t("Load")), alt.Tooltip("Hours:Q", title=t("Hours")),
                 alt.Tooltip("Power:Q", format=".1f", title="kW")],
    ).properties(height=260, title=t("Load duration curve"))
    return over_year, curve


def efficiency_curves(values: dict, operating: tuple[float, float] | None = None) -> tuple[alt.Chart, alt.Chart]:
    """COP (heating) and EER (cooling) against the average fluid temperature, as two charts so a high passive
    cooling EER does not flatten the COP curve. Optionally shades the fluid temperatures the design reaches."""
    from .properties.heat_pump import COP_TEMPS, EER_TEMPS, curves
    cop, eer = curves(values)
    charts = []
    for temps, vals, name, color in ((COP_TEMPS, cop, t("COP heating"), PIPE_DOWN),
                                     (EER_TEMPS, eer, t("EER cooling"), PIPE_UP)):
        data = pd.DataFrame({"T": temps, "Value": vals})
        line = alt.Chart(data).mark_line(point={"color": color}, color=color).encode(
            x=alt.X("T:Q", title=t("Average fluid temperature [°C]")),
            y=alt.Y("Value:Q", title=name, scale=alt.Scale(zero=False, padding=10), axis=alt.Axis(format=".1f")),
            tooltip=[alt.Tooltip("T:Q", title="°C"), alt.Tooltip("Value:Q", format=".2f", title=name)])
        title = name
        if operating is not None:
            band = alt.Chart(pd.DataFrame({"lo": [operating[0]], "hi": [operating[1]]})).mark_rect(
                opacity=0.15, color="#555").encode(x="lo:Q", x2="hi:Q")
            line = band + line
            title = t("{name} (grey: fluid temperatures of this design, {lo:.1f} to {hi:.1f} °C)", name=name,
                      lo=operating[0], hi=operating[1])
        charts.append(line.properties(height=220, title=title))
    return tuple(charts)


def heat_pump_yearly_chart(table: pd.DataFrame, show_spf: bool) -> alt.Chart | tuple:
    """Electricity per year, and the seasonal performance factor per year when it changes."""
    cols = {"Electricity heating [MWh]": t("Heating"), "Electricity cooling [MWh]": t("Cooling"),
            "Electricity hot water [MWh]": t("Hot water")}
    data = table[["Year", *cols]].rename(columns=cols).melt("Year", var_name="Use", value_name="MWh")
    data = data[data["MWh"] > 0]
    bars = alt.Chart(data).mark_bar().encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0), title=t("Year")),
        y=alt.Y("MWh:Q", title=t("Electricity [MWh/yr]"), stack=True),
        color=alt.Color("Use:N", scale=alt.Scale(domain=list(cols.values()), range=[PIPE_DOWN, PIPE_UP, "#e0a030"]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Year:O", title=t("Year")), alt.Tooltip("Use:N", title=t("Use")),
                 alt.Tooltip("MWh:Q", format=",.1f")],
    ).properties(height=260, title=t("Heat pump electricity per year"))
    if not show_spf:
        return bars
    spf = alt.Chart(table.dropna(subset=["SPF heating"])).mark_line(point={"color": PIPE_DOWN}, color=PIPE_DOWN).encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0), title=t("Year")),
        y=alt.Y("SPF heating:Q", title=t("SPF heating [-]"), scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("Year:O", title=t("Year")),
                 alt.Tooltip("SPF heating:Q", format=".2f", title=t("SPF heating"))],
    ).properties(height=220, title=t("Seasonal performance factor per year (falls as the ground cools)"))
    return bars, spf


# Which drawing belongs to which input. Each function gets all inputs, so it can
# combine sections (the borehole drawing needs the radius from "borefield").
DRAWINGS: dict[tuple[str, str], tuple[str, Callable[[dict[str, SectionInput]], object]]] = {
    ("ground", "constant"): ("Ground layers", ground_log_drawing),
    ("ground", "flux"): ("Ground layers", ground_log_drawing),
    ("ground", "gradient"): ("Ground layers", ground_log_drawing),
    ("borefield", "rectangular"): ("Borefield layout", lambda i: rectangular_layout(i["borefield"].values)),
    ("borefield", "custom"): ("Borefield layout", lambda i: custom_layout(i["borefield"].values)),
    ("pipe", "single_u"): ("Borehole cross-section",
                           lambda i: _u_tube_cross_section(i["pipe"].values, i["borefield"].values["r_b_mm"], 2)),
    ("pipe", "double_u"): ("Borehole cross-section",
                           lambda i: _u_tube_cross_section(i["pipe"].values, i["borefield"].values["r_b_mm"], 4)),
    ("pipe", "coaxial"): ("Borehole cross-section",
                          lambda i: _coaxial_cross_section(i["pipe"].values, i["borefield"].values["r_b_mm"])),
    ("load", "monthly"): ("Ground load", lambda i: load_profile(i["load"].values)),
    ("load", "annual_building"): ("Monthly demand", lambda i: annual_demand_chart(i["load"].values)),
    ("load", "hourly_building"): ("Hourly demand", lambda i: hourly_demand(i["load"].values)),
    ("heat_pump", "curve"): ("Heat pump efficiency", lambda i: efficiency_curves(i["heat_pump"].values)),
}


def input_drawings(inputs: dict[str, SectionInput]) -> list[tuple[str, object]]:
    """All drawings available for the current inputs, as (title, figure or chart, or a tuple of them)."""
    out = []
    for (section, variant), (title, draw) in DRAWINGS.items():
        if section in inputs and inputs[section].variant == variant:
            out.append((t(title), draw(inputs)))
    return out


# ---------------------------------------------------------------- results

# The mean fluid temperatures in the charts (the borehole wall temperature stays in the tables and the Excel export)
AVERAGE_COLUMNS = ["Average fluid (base load)", "Average fluid (peak extraction)", "Average fluid (peak injection)"]


@dataclass(frozen=True)
class ChartStyle:
    """What the temperature charts show. Set on the results page ("Customize the results") and used in the PDF too."""
    base: bool = True  # grey: the fluid without peaks
    peak_heat: bool = True  # blue: the fluid at the heating peaks
    peak_cool: bool = True  # red: the fluid at the cooling peaks
    limits: bool = True  # dashed lines at the temperature limits
    shading: bool = True  # light colour outside the limits
    limit_labels: bool = True  # "min. limit 0 °C" at the lines
    extremes: bool = True  # rings at the lowest and highest temperature
    pointer: bool = True  # the line that follows the pointer with all values

    @classmethod
    def from_dict(cls, d: dict | None) -> "ChartStyle":
        d = d or {}
        return cls(**{f.name: bool(d.get(f.name, f.default)) for f in fields(cls)})

    def series(self) -> list[str]:
        """The mean fluid temperatures switched on (at least one: the peaks when everything is off)."""
        on = [c for c, flag in zip(AVERAGE_COLUMNS, (self.base, self.peak_heat, self.peak_cool)) if flag]
        return on or AVERAGE_COLUMNS[1:]


DEFAULT_STYLE = ChartStyle()

# One colour per series in every chart: blue = cold side (heating peaks), red = warm side (cooling peaks).
SERIES_COLORS = {
    "Borehole wall": "#8c6d46",
    "Average fluid (base load)": "#8a8a8a",
    "Average fluid (peak extraction)": PIPE_UP,
    "Average fluid (peak injection)": PIPE_DOWN,
    "Into borefield (peak extraction)": "#1b4f72",
    "Out of borefield (peak extraction)": "#7cc0e0",
    "Into borefield (peak injection)": "#8e1b2c",
    "Out of borefield (peak injection)": "#ef9aa5",
    "Average fluid": PIPE_UP,
    "Lowest": PIPE_UP,
    "Highest": PIPE_DOWN,
}


def _series_color(series: list[str]) -> alt.Color:
    """Colours by the English series name; the legend shows the names in the current language."""
    return alt.Color("Series:N", scale=alt.Scale(domain=[t(s) for s in series],
                                                 range=[SERIES_COLORS.get(s, "#555") for s in series]),
                     legend=alt.Legend(orient="top", title=None, columns=2, labelLimit=260))


def _translate_series(data: pd.DataFrame) -> pd.DataFrame:
    data["Series"] = data["Series"].map(t)
    return data


def _limit_rules(limits: dict, field: str = "Temperature", labels: bool = True,
                 style: ChartStyle = DEFAULT_STYLE) -> alt.Chart | None:
    """Dashed lines at the temperature limits, labelled on the left, with the area outside them shaded. Parts can be
    switched off in ``style``; None when nothing is left."""
    if not (style.limits or style.shading):
        return None
    bounds = pd.DataFrame({field: [limits["T_min"], limits["T_max"]],
                           "Label": [t("min. limit {x:g} °C", x=limits["T_min"]),
                                     t("max. limit {x:g} °C", x=limits["T_max"])]})
    base = alt.Chart(bounds)
    # light shading outside the limits: red above the maximum, blue below the minimum
    above = alt.Chart(bounds.iloc[[1]]).mark_rect(color="#ef4444", opacity=0.08).encode(
        y=f"{field}:Q", y2=alt.value(0))
    below = alt.Chart(bounds.iloc[[0]]).mark_rect(color="#3b82f6", opacity=0.08).encode(
        y=f"{field}:Q", y2=alt.value("height"))
    line = base.mark_rule(strokeDash=[6, 4], color=NEUTRAL).encode(y=f"{field}:Q")
    rules = (above + below + line) if style.shading and style.limits else (above + below) if style.shading else line
    if not labels or not style.limits or not style.limit_labels:
        return rules
    text = base.mark_text(align="left", dx=4, dy=-7, fontSize=11, color=NEUTRAL).encode(
        y=f"{field}:Q", x=alt.value(0), text="Label:N")
    return rules + text


def _layers(*parts) -> alt.LayerChart | alt.Chart:
    """The parts that are not None, layered."""
    parts = [p for p in parts if p is not None]
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out


def when(years: float) -> str:
    """"year 50, January" for a time in years as in the monthly results (month k of the simulation at k/12)."""
    k = max(int(round(float(years) * 12)), 1)
    return t("year {year}, {month}", year=(k - 1) // 12 + 1, month=i18n.long_month((k - 1) % 12))


def _extreme_marks(data: pd.DataFrame, x: str, x_type: str = "Q", label=None) -> alt.Chart:
    """Rings at the lowest and highest temperature, labelled with the value (and with ``label(x)``, e.g. when)."""
    lo = data.loc[data["Temperature"].idxmin()]
    hi = data.loc[data["Temperature"].idxmax()]

    def text(row, name):
        value = fmt("{x:.1f} °C", x=round(row["Temperature"], 1) + 0.0)
        return t("{name}: {value} ({when})", name=t(name), value=value, when=label(row[x])) if label else value

    marks = pd.DataFrame({x: [lo[x], hi[x]], "Temperature": [lo["Temperature"], hi["Temperature"]],
                          "Label": [text(lo, "Lowest"), text(hi, "Highest")], "low": [1, 0],
                          "Colour": [SERIES_COLORS["Lowest"], SERIES_COLORS["Highest"]],
                          "align": ["right" if label and lo[x] > data[x].median() else "left",
                                    "right" if label and hi[x] > data[x].median() else "left"]})
    base = alt.Chart(marks).encode(x=f"{x}:{x_type}", y="Temperature:Q")
    ring = base.mark_point(size=110, strokeWidth=2.2, filled=False, opacity=1).encode(
        color=alt.Color("Colour:N", scale=None))
    out = ring
    for low, dy in ((1, 18), (0, -14)):
        for align, dx in (("left", 6), ("right", -6)):
            out += base.mark_text(fontSize=12, fontWeight="bold", dy=dy, dx=dx, align=align).encode(
                text="Label:N", color=alt.Color("Colour:N", scale=None)).transform_filter(
                f"datum.low == {low} && datum.align == '{align}'")
    return out


def _crosshair(wide: pd.DataFrame, x: str, x_type: str, columns: list[str], when_field: str | None = None,
               x_title: str = "", sort=None) -> alt.Chart:
    """A vertical line that follows the pointer and lists every series at that point, with the unit."""
    hover = alt.selection_point(fields=[x], nearest=True, on="pointerover", empty=False, clear="pointerout")
    names = {c: f"c{i}" for i, c in enumerate(columns)}  # plain field names: Altair dislikes brackets and dots
    data = wide.rename(columns=names)
    tips = [alt.Tooltip(f"{when_field}:N", title=x_title)] if when_field else \
        [alt.Tooltip(f"{x}:{x_type}", title=x_title)]
    tips += [alt.Tooltip(f"{names[c]}:Q", format=".2f", title=f"{t(c)} [°C]") for c in columns]
    return alt.Chart(data).mark_rule(color=NEUTRAL, strokeWidth=1).encode(
        x=alt.X(f"{x}:{x_type}", sort=sort), opacity=alt.condition(hover, alt.value(0.8), alt.value(0)), tooltip=tips,
    ).add_params(hover)


def temperature_domain(temps: pd.DataFrame, limits: dict, columns: list[str] | None = None) -> list[float]:
    """The temperature axis: the mean fluid temperatures shown and both limits, with room for the labels."""
    values = temps[columns or AVERAGE_COLUMNS].to_numpy()
    low, high = min(float(values.min()), limits["T_min"]), max(float(values.max()), limits["T_max"])
    pad = (high - low) * 0.1
    return [low - pad, high + pad]


def temperature_chart(temps: pd.DataFrame, limits: dict, period: tuple[float, float] | None = None,
                      style: ChartStyle = DEFAULT_STYLE) -> alt.Chart:
    """The mean fluid temperatures over the simulation, with the limits, the lowest and highest value and a
    line that shows all values at the pointer. ``period`` (from, to) in years shows a part only."""
    # Altair treats [ ] in field names specially, so units go in titles, not column names.
    columns = style.series()
    domain = temperature_domain(temps, limits, columns)
    temps = temps[columns]
    if period is not None:
        temps = temps[(temps.index >= period[0] - 1e-9) & (temps.index <= period[1] + 1e-9)]
    data = temps.reset_index().melt("Years", var_name="Series", value_name="Temperature")
    extremes = data[data["Series"].isin(["Average fluid (peak extraction)", "Average fluid (peak injection)"])]
    if extremes.empty:
        extremes = data
    data = _translate_series(data)
    x = alt.X("Years:Q", title=t("Time [years]"), scale=alt.Scale(nice=False, domain=[
        float(temps.index.min()) if period else 0.0, float(temps.index.max())]))
    lines = alt.Chart(data).mark_line(strokeWidth=1.6).encode(
        x=x, y=alt.Y("Temperature:Q", title=t("Mean fluid temperature [°C]"), scale=alt.Scale(domain=domain, nice=False)),
        color=_series_color(columns))
    wide = temps.reset_index()
    wide["When"] = [when(y) for y in wide["Years"]]
    hover = _crosshair(wide, "Years", "Q", columns, "When", t("Time")) if style.pointer else None
    marks = _extreme_marks(extremes.reset_index(drop=True), "Years", label=when) if style.extremes else None
    return _layers(lines, _limit_rules(limits, style=style), marks, hover).properties(
        height=500, title=t("Fluid temperature in the boreholes over {n} years", n=round(float(temps.index.max()))))


def last_year_chart(temps: pd.DataFrame, limits: dict, compact: bool = False,
                    style: ChartStyle = DEFAULT_STYLE) -> alt.Chart:
    """Zoom on the last simulated year, with supply and return temperatures when they are known. ``compact``: the
    mean temperatures only, small, to stand next to the chart over the years."""
    columns = style.series()
    domain = temperature_domain(temps, limits, columns)
    last = temps.tail(12).copy()
    if not compact and "Into borefield (peak extraction)" in last:
        kinds = [k for k, flag in (("extraction", style.peak_heat), ("injection", style.peak_cool)) if flag] or \
            ["extraction", "injection"]
        last = last[[c for c in last.columns if c.startswith(("Into", "Out of")) and any(k in c for k in kinds)]]
    else:
        last = last[columns]
    year = round(float(temps.index.max()))
    last.index = pd.Index(_months(), name="Month")
    data = _translate_series(last.reset_index().melt("Month", var_name="Series", value_name="Temperature"))
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Month:N", sort=_months(), title=None, axis=alt.Axis(labelAngle=-90 if compact else 0)),
        y=alt.Y("Temperature:Q", title=t("Mean fluid temperature [°C]") if not compact else None,
                scale=alt.Scale(domain=domain, nice=False) if compact else alt.Undefined),
        color=_series_color(list(last.columns)) if not compact else
        alt.Color("Series:N", scale=alt.Scale(domain=[t(s) for s in last.columns],
                                              range=[SERIES_COLORS[s] for s in last.columns]), legend=None),
    )
    hover = _crosshair(last.reset_index(), "Month", "N", list(last.columns), x_title=t("Month"), sort=_months()) \
        if style.pointer else None
    chart = _layers(lines, _limit_rules(limits, labels=not compact, style=style), hover)
    return chart.properties(height=440 if compact else 380,
                            title=t("Year {n} (zoom)", n=year) if compact else t("Last year of the simulation"))


def hourly_band_chart(hourly: pd.DataFrame, limits: dict, style: ChartStyle = DEFAULT_STYLE) -> alt.Chart:
    """Daily min-max band of the hourly fluid temperature over the whole simulation."""
    days = hourly["Average fluid"].groupby((hourly.index - 1) // 24).agg(["min", "max"])
    days["Years"] = ((days.index + 1) / 365).round(4)
    band = alt.Chart(days.round(2)).mark_area(opacity=0.5, color=PIPE_UP).encode(
        x=alt.X("Years:Q", title=t("Time [years]")),
        y=alt.Y("min:Q", title=t("Average fluid temperature [°C]")),
        y2="max:Q",
        tooltip=[alt.Tooltip("Years:Q", format=".2f", title=t("Years")),
                 alt.Tooltip("min:Q", format=".2f", title=t("Daily minimum °C")),
                 alt.Tooltip("max:Q", format=".2f", title=t("Daily maximum °C"))],
    )
    return _layers(band, _limit_rules(limits, style=style)).properties(
        height=380, title=t("Hourly fluid temperature (daily range)"))


def hourly_last_year_chart(hourly: pd.DataFrame, limits: dict, style: ChartStyle = DEFAULT_STYLE) -> alt.Chart:
    """The last simulated year: the fluid as a 3-hour min-max band (keeps every peak, a third of the points)."""
    last = hourly.tail(8760).reset_index(drop=True)
    agg = last.groupby(last.index // 3).agg(["min", "max", "mean"])
    data = pd.DataFrame({"Day": ((agg.index.to_numpy() * 3 + 1.5) / 24).round(3),
                         "min": agg[("Average fluid", "min")].round(2).to_numpy(),
                         "max": agg[("Average fluid", "max")].round(2).to_numpy()})
    x = alt.X("Day:Q", title=t("Day of the last year"), scale=alt.Scale(domain=[0, 365], nice=False))
    band = alt.Chart(data).mark_area(opacity=0.8, color=PIPE_UP).encode(
        x=x, y=alt.Y("min:Q", title=t("Temperature [°C]")), y2="max:Q",
        tooltip=[alt.Tooltip("Day:Q", format=".1f", title=t("Day")),
                 alt.Tooltip("min:Q", title=t("Fluid minimum °C")), alt.Tooltip("max:Q", title=t("Fluid maximum °C"))])
    return _layers(band, _limit_rules(limits, style=style)).properties(
        height=380, title=t("Hourly fluid temperature in the last year"))


# ---------------------------------------------------------------- post-processing

def yearly_extremes_chart(df: pd.DataFrame, limits: dict, style: ChartStyle = DEFAULT_STYLE) -> alt.Chart:
    data = _translate_series(df.melt("Year", var_name="Series", value_name="Temperature"))
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Year:O", title=t("Year"), axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Temperature:Q", title=t("Average fluid temperature [°C]")),
        color=_series_color(["Lowest", "Highest"]),
        tooltip=[alt.Tooltip("Year:O", title=t("Year")), alt.Tooltip("Series:N", title=t("Series")),
                 alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    return _layers(lines, _limit_rules(limits, style=style)).properties(
        height=320, title=t("Lowest and highest temperature per year"))


def _energy_text(value: float, top: float) -> str:
    return fmt("{x:,.1f}", x=value) if top < 20 else fmt("{x:,.0f}", x=value)


def energy_balance_chart(df: pd.DataFrame) -> alt.Chart:
    """Energy taken from (below zero) and returned to the ground (above zero) per month, the value on every bar,
    and the net balance of each month as a line."""
    ext, inj, net = t("Taken from the ground (cools it)"), t("Returned to the ground (warms it)"), t("Net balance")
    months = _month_names(df["Month"])
    top = float(max(df["Extraction"].max(), df["Injection"].max(), 0.0))
    bars = pd.DataFrame({"Month": months * 2,
                         "Energy": [-float(x) for x in df["Extraction"]] + [float(x) for x in df["Injection"]],
                         "Type": [ext] * 12 + [inj] * 12})
    bars["Label"] = [_energy_text(abs(v), top) if abs(v) >= top * 0.005 and abs(v) > 0 else "" for v in bars["Energy"]]
    line = pd.DataFrame({"Month": months, "Energy": (df["Injection"] - df["Extraction"]).astype(float).to_list(),
                         "Type": [net] * 12})
    colour = alt.Color("Type:N", scale=alt.Scale(domain=[ext, inj, net], range=[EXTRACTION, INJECTION, NEUTRAL]),
                       legend=alt.Legend(orient="top", title=None, labelLimit=300, columns=1))
    x = alt.X("Month:N", sort=_months(), title=None, axis=alt.Axis(labelAngle=0))
    tip = [alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Type:N", title=" "),
           alt.Tooltip("Energy:Q", format=",.1f", title="MWh")]
    base = alt.Chart(bars).encode(x=x, y=alt.Y("Energy:Q", title=t("Energy per month [MWh]")))
    chart = base.mark_bar(opacity=0.9).encode(color=colour, tooltip=tip)
    for sign, dy, baseline in (("<", 4, "top"), (">", -4, "bottom")):
        chart += base.mark_text(fontSize=11, dy=dy, baseline=baseline).encode(
            text="Label:N", color=alt.Color("Type:N", scale=alt.Scale(domain=[ext, inj, net],
                                                                      range=[EXTRACTION, INJECTION, NEUTRAL]),
                                            legend=None)).transform_filter(f"datum.Energy {sign} 0")
    chart += alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=NEUTRAL).encode(y="y:Q")
    chart += alt.Chart(line).mark_line(point=alt.OverlayMarkDef(size=40, filled=True), strokeWidth=1.8).encode(
        x=x, y="Energy:Q", color=colour, tooltip=tip)
    imbalance = float(df["Injection"].sum() - df["Extraction"].sum())
    return chart.properties(height=440, title=t("Energy taken from and returned to the ground (year balance "
                                                "{x:+,.0f} MWh)", x=imbalance))


def heatmap_chart(hourly: pd.DataFrame) -> alt.Chart:
    """Average fluid temperature in the last year: day of the year against hour of the day."""
    last = hourly["Average fluid"].tail(8760).to_numpy()
    data = pd.DataFrame({"Day": [h // 24 + 1 for h in range(8760)], "Hour": [h % 24 for h in range(8760)],
                         "Temperature": last})
    return alt.Chart(data).mark_rect().encode(
        x=alt.X("Day:O", title=t("Day of the last year"), axis=alt.Axis(values=list(range(1, 366, 30)), labelAngle=0)),
        y=alt.Y("Hour:O", title=t("Hour of the day"), axis=alt.Axis(values=[0, 6, 12, 18])),
        color=alt.Color("Temperature:Q", scale=alt.Scale(scheme="redyellowblue", reverse=True),
                        title="°C"),
        tooltip=[alt.Tooltip("Day:O", title=t("Day")), alt.Tooltip("Hour:O", title=t("Hour")),
                 alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    ).properties(height=300, title=t("When it gets cold or warm (average fluid temperature, last year)"))


def tornado_chart(df: pd.DataFrame) -> alt.Chart:
    base = float(df["Base"].iloc[0])
    rows = []
    lower, higher = t("Lower input"), t("Higher input")
    for _, r in df.iterrows():
        # in percent, so the chart also reads right when the result itself was sized hourly
        rows.append({"Input": t(r["Input"]), "Case": lower, "Delta": (r["Low"] / base - 1) * 100, "Length": r["Low"]})
        rows.append({"Input": t(r["Input"]), "Case": higher, "Delta": (r["High"] / base - 1) * 100,
                     "Length": r["High"]})
    data = pd.DataFrame(rows)
    return alt.Chart(data).mark_bar().encode(
        y=alt.Y("Input:N", sort=[t(x) for x in df["Input"]], title=None, axis=alt.Axis(labelLimit=260)),
        yOffset=alt.YOffset("Case:N"),
        x=alt.X("Delta:Q", title=t("Change in borehole length [%]")),
        color=alt.Color("Case:N", scale=alt.Scale(domain=[lower, higher], range=[PIPE_UP, PIPE_DOWN]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Input:N", title=t("Input")), alt.Tooltip("Case:N", title=t("Case")),
                 alt.Tooltip("Length:Q", format=".1f", title=t("Length m")),
                 alt.Tooltip("Delta:Q", format="+.1f", title=t("Change %"))],
    ).properties(height=alt.Step(18), title=t("What the borehole length depends on most"))


def comparison_chart(df: pd.DataFrame, column: str, title: str) -> alt.Chart:
    # Altair cannot use field names with brackets, so the column is copied to a plain name
    data = pd.DataFrame({"Variant": df["Variant"], "Value": df[column]})
    return alt.Chart(data).mark_bar(color=PIPE_UP).encode(
        x=alt.X("Value:Q", title=title),
        y=alt.Y("Variant:N", sort=None, title=None, axis=alt.Axis(labelLimit=200)),
        tooltip=[alt.Tooltip("Variant:N", title=t("Variant")), alt.Tooltip("Value:Q", format=",.1f", title=title)],
    ).properties(height=alt.Step(28))


def gfunction_chart(df: pd.DataFrame) -> alt.Chart:
    return alt.Chart(df).mark_line(color=PIPE_UP).encode(
        x=alt.X("ln_t_ts:Q", title="ln(t/ts)"),
        y=alt.Y("g:Q", title=t("g-function")),
        tooltip=[alt.Tooltip("hours:Q", format=",.0f", title=t("Time h")),
                 alt.Tooltip("g:Q", format=".3f", title=t("g-function"))],
    ).properties(height=300, title=t("g-function of the borefield (thermal interaction of the boreholes)"))


def load_duration_chart(df: pd.DataFrame) -> alt.Chart:
    """Building demand and ground load, each sorted from the highest hour to the lowest."""
    cols = [c for c in df.columns if c != "Hours"]
    data = df.iloc[::10].melt("Hours", value_vars=cols, var_name="Load", value_name="Power")
    data["Load"] = data["Load"].map(t)
    colors = {"Heating demand": HEATING, "Cooling demand": COOLING, "Ground extraction": "#95c4d9",
              "Ground injection": "#f2a3ad"}
    dashes = {"Ground extraction": [5, 3], "Ground injection": [5, 3]}
    names = [t(c) for c in cols]
    return alt.Chart(data).mark_line().encode(
        x=alt.X("Hours:Q", title=t("Hours per year"), scale=alt.Scale(domain=[0, 8760])),
        y=alt.Y("Power:Q", title=t("Power [kW]")),
        color=alt.Color("Load:N", scale=alt.Scale(domain=names, range=[colors.get(c, "#555") for c in cols]),
                        legend=alt.Legend(orient="top", title=None)),
        strokeDash=alt.StrokeDash("Load:N", scale=alt.Scale(domain=names, range=[dashes.get(c, [1, 0]) for c in cols]),
                                  legend=None),
        tooltip=[alt.Tooltip("Load:N", title=t("Load")), alt.Tooltip("Hours:Q", title=t("Hours")),
                 alt.Tooltip("Power:Q", format=",.1f", title="kW")],
    ).properties(height=300, title=t("Load duration curve (first year)"))


def pressure_drop_chart(df: pd.DataFrame, flow: float, dp: float) -> alt.Chart:
    data = pd.DataFrame({"Flow": df["Flow per borehole [l/s]"], "Drop": df["Pressure drop [kPa]"]})
    line = alt.Chart(data).mark_line(color=PIPE_UP).encode(
        x=alt.X("Flow:Q", title=t("Flow rate per borehole [l/s]")),
        y=alt.Y("Drop:Q", title=t("Pressure drop per borehole [kPa]")),
        tooltip=[alt.Tooltip("Flow:Q", format=".3f", title="l/s"), alt.Tooltip("Drop:Q", format=".1f", title="kPa")])
    point = pd.DataFrame({"Flow": [flow], "Drop": [dp], "Label": [t("design: {dp:.1f} kPa", dp=dp)]})
    base = alt.Chart(point).encode(x="Flow:Q", y="Drop:Q")
    return (line + base.mark_point(filled=True, size=80, color=NEUTRAL)
            + base.mark_text(align="left", dx=8, dy=-8, fontWeight="bold", color=NEUTRAL).encode(text="Label:N")).properties(
        height=300, title=t("Pressure drop against flow rate"))


def _nice_step(span: float, classes: int = 10) -> float:
    """A round step (1, 2, 2.5 or 5 × 10^n) that splits ``span`` into about ``classes`` parts."""
    raw = max(span, 1e-6) / classes
    power = 10 ** np.floor(np.log10(raw))
    return float(min((m * power for m in (1, 2, 2.5, 5, 10) if m * power >= raw), default=10 * power))


def ground_classes(changes) -> tuple[float, list[float]]:
    """Step and the isoline levels (multiples of the step, without 0) for the ground temperature changes."""
    lo, hi = float(np.min(changes)), float(np.max(changes))
    step = _nice_step(hi - lo)
    levels = [round(v, 6) for v in np.arange(np.floor(lo / step) * step, hi + step * 1e-6, step)
              if lo < v < hi and abs(v) > step * 1e-6]
    return step, levels


def _diverging(value: float, lim: float) -> str:
    from matplotlib import colormaps
    from matplotlib.colors import to_hex
    return to_hex(colormaps["RdBu_r"](0.5 + 0.5 * float(np.clip(value / lim, -1, 1)) * 0.92))


def _square_domain(xs, ys) -> tuple[list[float], list[float]]:
    """Axis ranges of the same length, so one metre is as long in x as in y."""
    span = max(xs.max() - xs.min(), ys.max() - ys.min())
    cx, cy = (xs.max() + xs.min()) / 2, (ys.max() + ys.min()) / 2
    return [cx - span / 2, cx + span / 2], [cy - span / 2, cy + span / 2]


def _scale_bar_length(span: float) -> float:
    target = span / 5
    return float(max((v for v in (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000) if v <= target), default=1))


def ground_map_chart(m: dict, north: bool = False, size: int = 420) -> alt.Chart:
    """Ground temperature change at mid-depth around the field at the end of the simulation: colour classes,
    labelled isolines, the boreholes, a scale bar and (for real coordinates) north."""
    import contourpy
    table, holes, cell = m["table"], m["boreholes"], m["cell"]
    gx, gy = np.sort(table["x"].unique()), np.sort(table["y"].unique())
    grid = table.pivot(index="y", columns="x", values="Change").loc[gy, gx].to_numpy()
    step, levels = ground_classes(grid)
    lim = max(abs(float(grid.min())), abs(float(grid.max())), step)
    bounds = [levels[0] - step] + levels + [levels[-1] + step] if levels else [float(grid.min()), float(grid.max())]
    colours = [_diverging((a + b) / 2, lim) for a, b in zip(bounds[:-1], bounds[1:])]
    dom_x, dom_y = _square_domain(gx, gy)
    decimals = 0 if step >= 1 else (1 if step >= 0.1 else 2)
    colour = alt.Color("Change:Q", title=t("Change [K]"),
                       scale=alt.Scale(type="threshold", domain=levels, range=colours) if levels else
                       alt.Scale(range=colours[:1] * 2),
                       legend=alt.Legend(format=f"+.{decimals}f", orient="right" if size >= 400 else "bottom",
                                         direction="vertical" if size >= 400 else "horizontal"))
    half = cell * 0.6  # a little overlap, so no seams show between the cells
    # cell edges and the temperature are calculated in the browser: a third of the data to send to a phone
    cells = table[["x", "y", "Change"]].round({"x": 2, "y": 2, "Change": 4})
    heat = alt.Chart(cells).transform_calculate(
        x1=f"datum.x - {half}", x2=f"datum.x + {half}", y1=f"datum.y - {half}", y2=f"datum.y + {half}",
        Temperature=f"datum.Change + {float(m['t_ground'])}").mark_rect().encode(
        x=alt.X("x1:Q", title="x [m]", scale=alt.Scale(domain=dom_x, nice=False), axis=alt.Axis(grid=False)),
        x2="x2:Q",
        y=alt.Y("y1:Q", title="y [m]", scale=alt.Scale(domain=dom_y, nice=False), axis=alt.Axis(grid=False)),
        y2="y2:Q", color=colour,
        tooltip=[alt.Tooltip("x:Q", format=".0f", title="x [m]"), alt.Tooltip("y:Q", format=".0f", title="y [m]"),
                 alt.Tooltip("Change:Q", format="+.2f", title=t("Change K")),
                 alt.Tooltip("Temperature:Q", format=".2f", title=t("Ground °C"))])
    # isolines at every class boundary, with a label at the top of each line
    gen = contourpy.contour_generator(gx, gy, grid)
    rows, ends = [], []
    for level in levels:
        top = right = None
        for seg, line in enumerate(gen.lines(level)):
            if len(line) < 4:
                continue
            for order, (px, py) in enumerate(line):
                rows.append({"x": px, "y": py, "Line": f"{level}/{seg}", "order": order})
            t_, r_ = line[np.argmax(line[:, 1])], line[np.argmax(line[:, 0])]
            top = t_ if top is None or t_[1] > top[1] else top
            right = r_ if right is None or r_[0] > right[0] else right
        if top is not None:
            ends.append((level, top, right))
    # a label at the top of each line; where lines lie close together, at the right end instead, or none
    labels, gap = [], (dom_y[1] - dom_y[0]) * 0.04
    used_top, used_right = [], []
    for level, top, right in ends:
        if all(abs(top[1] - y_) > gap for y_ in used_top):
            spot = top
            used_top.append(top[1])
        elif all(abs(right[0] - x_) > gap * 1.6 for x_ in used_right):
            spot = right
            used_right.append(right[0])
        else:
            continue
        labels.append({"x": spot[0], "y": spot[1], "Label": fmt(f"{{v:+.{decimals}f}} K", v=level),
                       "dark": abs(level) > 0.55 * lim})
    out = heat
    if rows:
        out += alt.Chart(pd.DataFrame(rows)).mark_line(color="#1f2937", strokeWidth=0.8, opacity=0.75).encode(
            x="x:Q", y="y:Q", detail="Line:N", order="order:Q")
    out += alt.Chart(holes).mark_point(shape="circle", size=10, color="black", filled=True, opacity=0.9).encode(
        x="x:Q", y="y:Q", tooltip=[alt.Tooltip("x:Q", format=".1f"), alt.Tooltip("y:Q", format=".1f")])
    if labels:
        lab = alt.Chart(pd.DataFrame(labels)).encode(x="x:Q", y="y:Q", text="Label:N")
        out += lab.mark_text(fontSize=10, fontWeight="bold", dy=-6, color="#ffffff").transform_filter("datum.dark")
        out += lab.mark_text(fontSize=10, fontWeight="bold", dy=-6, color="#1f2937").transform_filter("!datum.dark")
    # scale bar, bottom right
    span = dom_x[1] - dom_x[0]
    length = _scale_bar_length(span)
    bx1, by = dom_x[1] - span * 0.05, dom_y[0] + span * 0.05
    bar = pd.DataFrame({"x": [bx1 - length], "x2": [bx1], "y": [by], "Label": [fmt("{v:g} m", v=length)]})
    out += alt.Chart(bar).mark_rule(strokeWidth=3, color="#111827").encode(x="x:Q", x2="x2:Q", y="y:Q")
    out += alt.Chart(bar.assign(xm=(bar["x"] + bar["x2"]) / 2)).mark_text(dy=-9, fontSize=11, color="#111827").encode(
        x="xm:Q", y="y:Q", text="Label:N")
    if north:
        arrow = pd.DataFrame({"x": [dom_x[0] + span * 0.06], "y": [dom_y[1] - span * 0.07]})
        out += alt.Chart(arrow).mark_point(shape="triangle-up", size=160, filled=True, color="#111827").encode(
            x="x:Q", y="y:Q")
        out += alt.Chart(arrow).mark_text(text="N", dy=16, fontWeight="bold", fontSize=12, color="#111827").encode(
            x="x:Q", y="y:Q")
    # "pad": the plot itself is size × size, so one metre is as long in x as in y; axes and legend come on top
    return out.properties(width=size, height=size, autosize=alt.AutoSizeParams(type="pad"),
                          title=t("Ground temperature change at {depth:.0f} m depth after {years} years",
                                  depth=m["depth"], years=m["years"]))


def optimisation_chart(monthly: pd.DataFrame) -> alt.Chart:
    """Average monthly building demand split into the part the ground covers and the external part."""
    rows = []
    for _, r in monthly.iterrows():
        month = _month_names([r["Month"]])[0]
        for kind, sign in (("heating", 1), ("cooling", -1)):
            rows.append({"Month": month, "Part": t(f"Ground {kind}"), "Energy": sign * r[f"Ground {kind} [MWh]"]})
            rows.append({"Month": month, "Part": t(f"Backup {kind}"), "Energy": sign * r[f"External {kind} [MWh]"]})
    data = pd.DataFrame(rows)
    parts = [t("Ground heating"), t("Backup heating"), t("Ground cooling"), t("Backup cooling")]
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=_months(), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title=t("Building demand [MWh] (cooling below zero)")),
        color=alt.Color("Part:N", scale=alt.Scale(domain=parts, range=[HEATING, "#f2c4ca", COOLING, "#bcdbe8"]),
                        legend=alt.Legend(orient="top", title=None)),
        order=alt.Order("Part:N"),
        tooltip=[alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Part:N", title=t("Share")),
                 alt.Tooltip("Energy:Q", format=",.1f", title="MWh")],
    ).properties(height=320, title=t("Who covers the demand (average year)"))


def borehole_map_chart(table: pd.DataFrame, colour: str) -> alt.Chart:
    """Each borehole drawn at its position, coloured by its share of the load ("share") or by the long-term
    change of its wall temperature ("change")."""
    pad = max(table["x"].max() - table["x"].min(), table["y"].max() - table["y"].min(), 10.0) * 0.08 + 3
    lo_x, lo_y = table["x"].min() - pad, table["y"].min() - pad
    span = max(table["x"].max() - lo_x, table["y"].max() - lo_y) + pad  # same scale in x and y
    if colour == "share":
        field, title, fmt_ = "Percent", t("Share of the load [%]"), ".0f"
        data = table.assign(Percent=table["Share"] * 100)
        lim = max(abs(data["Percent"] - 100).max(), 1.0)
        scale = alt.Scale(scheme="redblue", reverse=True, domain=[100 - lim, 100 + lim])
    else:
        field, title, fmt_ = "Change", t("Change [K]"), "+.2f"
        data = table
        lim = max(table["Change"].abs().max(), 0.1)
        scale = alt.Scale(scheme="redblue", reverse=True, domain=[-lim, lim])
    size = float(np.clip(40000 / max(len(table), 1), 30, 500))
    return alt.Chart(data).mark_circle(size=size, opacity=1, stroke="white", strokeWidth=0.5).encode(
        x=alt.X("x:Q", title="x [m]", scale=alt.Scale(domain=[lo_x, lo_x + span], nice=False)),
        y=alt.Y("y:Q", title="y [m]", scale=alt.Scale(domain=[lo_y, lo_y + span], nice=False)),
        color=alt.Color(f"{field}:Q", title=title, scale=scale),
        tooltip=[alt.Tooltip("Borehole:Q", title=t("Borehole")),
                 alt.Tooltip("Percent:Q" if colour == "share" else "Change:Q", format=fmt_, title=title),
                 alt.Tooltip("x:Q", format=".1f"), alt.Tooltip("y:Q", format=".1f")],
    ).properties(width=440, height=440)
