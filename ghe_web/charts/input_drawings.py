"""Drawings of the inputs, shown beside the input fields: borefield layout, borehole cross-section, borehole log
and the load profiles. No Streamlit code here, so they can be tested on their own.

The drawings are looked up per (section, variant) in DRAWINGS, so a new variant (e.g. a coaxial pipe) only needs a
new entry to get its own picture.
"""
from __future__ import annotations

from typing import Callable

import altair as alt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from ghe_web.i18n import fmt, t  # noqa: E402
from ghe_web.inputs import SectionInput  # noqa: E402
from ghe_web.charts.palette import (EXTRACTION, GROUND, GROUT, INJECTION, PIPE_DOWN, PIPE_UP,  # noqa: E402
                                    load_colors, month_order)


def rectangular_layout(values: dict) -> plt.Figure:
    xs = [i * values["B_1"] for i in range(values["N_1"]) for _ in range(values["N_2"])]
    ys = [j * values["B_2"] for _ in range(values["N_1"]) for j in range(values["N_2"])]
    return borefield_layout(xs, ys, t("{n} boreholes, {b1:g} m × {b2:g} m spacing", n=len(xs), b1=values["B_1"],
                                      b2=values["B_2"]))


def custom_layout(values: dict) -> plt.Figure:
    from ghe_web.core.geometry import closest_pair
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
    from ghe_web.inputs.ground import layered
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
    from ghe_web.strata import predict, rocks
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
    from ghe_web.strata import predict
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
    from ghe_web.strata import rocks
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
        "Month": month_order() * 2,
        "Energy": [-float(x) for x in values["baseload_extraction"]]
                  + [float(x) for x in values["baseload_injection"]],
        "Type": [ext] * 12 + [inj] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=month_order(), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title=t("Energy [kWh] (extraction below zero)")),
        color=alt.Color("Type:N", scale=alt.Scale(domain=[ext, inj], range=[EXTRACTION, INJECTION]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=[alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Type:N", title=t("Load")),
                 alt.Tooltip("Energy:Q", format=",.0f", title="kWh")],
    ).properties(height=300, title=t("Monthly ground load"))


def annual_demand_chart(values: dict) -> alt.Chart:
    from ghe_web.inputs.load import _annual_to_monthly
    heat, cool, heat_peak, cool_peak = _annual_to_monthly(values)
    heating, cooling = t("Heating demand"), t("Cooling demand")
    data = pd.DataFrame({
        "Month": month_order() * 2,
        "Energy": [h / 1000 for h in heat] + [-c / 1000 for c in cool],
        "Peak": heat_peak + [-c for c in cool_peak],
        "Type": [heating] * 12 + [cooling] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=month_order(), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title=t("Building demand [MWh]")),
        color=alt.Color("Type:N", scale=load_colors(heating, cooling), legend=alt.Legend(orient="top", title=None)),
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
    colors = load_colors(heating, cooling)
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
    from ghe_web.inputs.heat_pump import COP_TEMPS, EER_TEMPS, curves
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
