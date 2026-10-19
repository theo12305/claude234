"""Drawings and charts of a well design. No Streamlit code here."""
from __future__ import annotations

import math

import altair as alt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .. import i18n  # noqa: E402
from ..i18n import fmt, t  # noqa: E402
from ..plots import COOLING, HEATING, NEUTRAL  # noqa: E402
from .design import Design  # noqa: E402
from .hydraulics import cone  # noqa: E402
from .thermal import plume  # noqa: E402

WATER = "#1565c0"
PRODUCTION = HEATING
INJECTION = COOLING


COMPASS = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def _compass(direction: float) -> str:
    return t(COMPASS[int((direction % 360) / 45 + 0.5) % 8])


def site_map(d: Design, aquifer: dict, years: int | None = None) -> plt.Figure:
    """Top view in the direction of the groundwater flow: wells, streamlines of the injected water, the drawdown
    cone and the temperature plume."""
    xs_w = [w.x for w in d.wells]
    ys_w = [w.y for w in d.wells]
    span = max(max(xs_w) - min(xs_w), max(ys_w) - min(ys_w), d.distance, 10.0)
    x0, x1 = min(xs_w) - 1.2 * span, max(xs_w) + 2.5 * span
    y0, y1 = min(ys_w) - 1.2 * span, max(ys_w) + 1.2 * span
    xs, ys = np.linspace(x0, x1, 220), np.linspace(y0, y1, 160)
    fig, ax = plt.subplots(figsize=(8, 5.2))

    years = years or int(d.temperatures["year"].max())
    if d.heat_net_w:
        inj = [w for w in d.wells if w.q < 0]
        cx, cy = np.mean([w.x for w in inj]), np.mean([w.y for w in inj])
        dt = plume(d.heat_net_w, aquifer["thickness"], d.c_aquifer, d.k_aquifer, d.darcy, aquifer["alpha_l"],
                   aquifer["alpha_t"], years, xs - cx, ys - cy)
        levels = [lv for lv in (0.5, 1, 2, 3) if lv < np.abs(dt).max()]
        if levels:
            cmap = "Blues" if d.heat_net_w < 0 else "Reds"
            ax.contourf(xs, ys, np.abs(dt), levels=levels + [max(np.abs(dt).max(), levels[-1] + 1e-6)], cmap=cmap,
                        alpha=0.35)
            cs = ax.contour(xs, ys, np.abs(dt), levels=levels, colors=COOLING if d.heat_net_w < 0 else HEATING,
                            linewidths=0.8)
            ax.clabel(cs, fmt=lambda v: fmt("{x:g} K", x=v), fontsize=7)

    s = cone(d.wells, aquifer["kf"] * aquifer["thickness"], 0.2, xs, ys)
    lim = max(0.05, float(np.nanpercentile(np.abs(s), 98)))
    step = 10 ** math.floor(math.log10(lim / 4))
    levels = [lv for lv in np.arange(-lim, lim + step, step) if abs(lv) > step / 2]
    if len(levels) > 1:
        ax.contour(xs, ys, s, levels=sorted(levels), colors=NEUTRAL, linewidths=0.5, linestyles="dotted")

    for path in d.streamlines.paths:
        if len(path) > 1:
            ax.plot(path[:, 0], path[:, 1], color=WATER, linewidth=0.6, alpha=0.6)
    for w in d.wells:
        prod = w.q > 0
        ax.plot(w.x, w.y, "o", markersize=9, color=PRODUCTION if prod else INJECTION, markeredgecolor="black",
                zorder=5)
    ax.plot([], [], "o", color=PRODUCTION, markeredgecolor="black", label=t("Production well"))
    ax.plot([], [], "o", color=INJECTION, markeredgecolor="black", label=t("Injection well"))
    ax.plot([], [], color=WATER, linewidth=0.8, label=t("Path of the injected water"))
    ax.plot([], [], color=NEUTRAL, linestyle="dotted", label=t("Drawdown / rise (lines)"))
    ax.annotate("", xy=(x0 + 0.22 * (x1 - x0), y1 - 0.08 * (y1 - y0)), xytext=(x0 + 0.04 * (x1 - x0),
                y1 - 0.08 * (y1 - y0)), arrowprops=dict(arrowstyle="-|>", color=WATER, lw=2))
    ax.text(x0 + 0.04 * (x1 - x0), y1 - 0.13 * (y1 - y0),
            t("Groundwater flow to {dir} ({deg:g}°), {v:.2f} m/day", dir=_compass(aquifer["direction"]),
              deg=aquifer["direction"], v=d.darcy / aquifer["porosity"] * 86400), color=WATER, fontsize=8, va="top")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xlabel(t("Along the flow [m]"))
    ax.set_ylabel(t("Across the flow [m]"))
    ax.legend(loc="lower right", fontsize=7.5, framealpha=0.9)
    ax.set_title(t("Wells, flow paths and temperature plume after {y} years", y=years), fontsize=10, loc="left")
    fig.tight_layout()
    return fig


def well_section(d: Design, aquifer: dict, rows: list[dict] | None = None) -> plt.Figure:
    """Well construction drawing (Ausbauplan) of a production and an injection well with the water levels."""
    from ..strata import rocks
    depth = d.screen.depth
    deepest = depth * 1.08 + 1
    fig, ax = plt.subplots(figsize=(7, 6.4))
    if rows:
        for i, r in enumerate(rows):
            top, bottom = float(r["top"]), float(r["bottom"]) if i < len(rows) - 1 else deepest
            if top >= deepest:
                break
            ax.add_patch(plt.Rectangle((0, top), 10, min(bottom, deepest) - top, facecolor=rocks.color(r["rock"]),
                                       hatch=rocks.hatch(r["rock"]), edgecolor="#00000033", linewidth=0.4, alpha=0.55))
            ax.text(10.15, (top + min(bottom, deepest)) / 2, t(r["rock"]), fontsize=7, va="center")
    else:
        ax.add_patch(plt.Rectangle((0, 0), 10, aquifer["top"], facecolor="#e8e2d0", alpha=0.7))
        ax.add_patch(plt.Rectangle((0, aquifer["top"]), 10, aquifer["bottom"] - aquifer["top"],
                                   facecolor="#f4d35e", hatch="..", alpha=0.45, edgecolor="#00000022"))
        ax.add_patch(plt.Rectangle((0, aquifer["bottom"]), 10, deepest - aquifer["bottom"], facecolor="#90a4ae",
                                   hatch="--", alpha=0.45, edgecolor="#00000022"))
        ax.text(10.15, (aquifer["top"] + aquifer["bottom"]) / 2, t("Aquifer"), fontsize=8, va="center")
        ax.text(10.15, (aquifer["bottom"] + deepest) / 2, t("Aquiclude"), fontsize=8, va="center")
    wd = aquifer["water_depth"]
    for x, name, level, color in ((2.5, t("Production well"), wd + d.peak.drawdown, PRODUCTION),
                                  (7.5, t("Injection well"), wd - d.peak.rise, INJECTION)):
        ax.add_patch(plt.Rectangle((x - 0.9, 0), 1.8, depth, facecolor="#d9cfb8", edgecolor="#555", linewidth=0.6))
        ax.add_patch(plt.Rectangle((x - 0.9, d.screen.top), 1.8, d.screen.length, facecolor="#e6c79c",
                                   hatch="oo", edgecolor="#555", linewidth=0.6))
        ax.add_patch(plt.Rectangle((x - 0.9, 0), 1.8, min(3.0, d.screen.top), facecolor="#8d8d8d", alpha=0.8))
        ax.add_patch(plt.Rectangle((x - 0.45, 0), 0.9, d.screen.top, facecolor="white", edgecolor="black", lw=1))
        ax.add_patch(plt.Rectangle((x - 0.45, d.screen.top), 0.9, d.screen.length, facecolor="white",
                                   edgecolor="black", lw=1, hatch="---"))
        ax.add_patch(plt.Rectangle((x - 0.45, d.screen.bottom), 0.9, depth - d.screen.bottom, facecolor="#cfcfcf",
                                   edgecolor="black", lw=1))
        ax.plot([x - 0.45, x + 0.45], [level, level], color=WATER, lw=2, zorder=5)
        ax.text(x, -0.5, name, ha="center", va="bottom", fontsize=8.5, weight="bold", color=color)
        ax.text(x + 1.0, level, fmt("{x:.1f} m", x=level), fontsize=7, color=WATER, va="center")
    ax.add_patch(plt.Rectangle((2.5 - 0.3, d.pump_depth - 0.8), 0.6, 1.6, facecolor=PRODUCTION, zorder=6))
    ax.text(2.5 - 1.05, d.pump_depth, t("Pump"), fontsize=7, ha="right", va="center")
    ax.plot([0, 10], [wd, wd], color=WATER, lw=1, linestyle="--")
    ax.text(5, wd, t("rest water level {x:.1f} m", x=wd), color=WATER, fontsize=7, ha="center", va="bottom")
    for y, label in ((d.screen.top, t("screen {a:.1f}–{b:.1f} m", a=d.screen.top, b=d.screen.bottom)),
                     (depth, t("depth {x:.1f} m", x=depth))):
        ax.text(5, y, label, fontsize=7, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1))
    ax.set_xlim(0, 13)
    ax.set_ylim(deepest, -2)
    ax.set_xticks([])
    ax.set_ylabel(t("Depth below ground [m]"))
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.set_title(t("Well construction (not to scale across)"), fontsize=10, loc="left")
    fig.tight_layout()
    return fig


def temperature_chart(d: Design, limits: dict) -> alt.Chart:
    data = d.temperatures.copy()
    data["Years"] = data["year"] - 1 + (data["month"] - 0.5) / 12
    data = data[data["active"]]
    long = pd.concat([pd.DataFrame({"Years": data["Years"], "Temperature": data["production"],
                                    "Series": t("Production well")}),
                      pd.DataFrame({"Years": data["Years"], "Temperature": data["injection"],
                                    "Series": t("Injection well")})])
    color = alt.Color("Series:N", scale=alt.Scale(domain=[t("Production well"), t("Injection well")],
                                                  range=[PRODUCTION, INJECTION]),
                      legend=alt.Legend(orient="top", title=None))
    lines = alt.Chart(long).mark_line(strokeWidth=1.4).encode(
        x=alt.X("Years:Q", title=t("Time [years]")), y=alt.Y("Temperature:Q", title=t("Temperature [°C]"),
                                                            scale=alt.Scale(zero=False)),
        color=color, tooltip=[alt.Tooltip("Series:N", title=t("Series")),
                              alt.Tooltip("Years:Q", format=".2f", title=t("Years")),
                              alt.Tooltip("Temperature:Q", format=".2f", title="°C")])
    bounds = pd.DataFrame({"Temperature": [limits["t_inj_min"], limits["t_inj_max"]],
                           "Label": [t("min. injection {x:g} °C", x=limits["t_inj_min"]),
                                     t("max. injection {x:g} °C", x=limits["t_inj_max"])]})
    rules = alt.Chart(bounds).mark_rule(strokeDash=[6, 4], color=NEUTRAL).encode(y="Temperature:Q")
    text = alt.Chart(bounds).mark_text(align="right", dx=-4, dy=-7, fontSize=11, color=NEUTRAL).encode(
        y="Temperature:Q", x=alt.value("width"), text="Label:N")
    return (lines + rules + text).properties(height=360, title=t("Water temperatures in the months the system runs"))


def monthly_chart(d: Design) -> alt.Chart:
    names = list(i18n.months())
    m = d.monthly
    data = pd.DataFrame({"Month": names, "Volume": m["volume_m3"], "Pump": m["pump_kwh"]})
    bars = alt.Chart(data).mark_bar(color=WATER).encode(
        x=alt.X("Month:N", sort=names, title=None), y=alt.Y("Volume:Q", title=t("Pumped water [m³]")),
        tooltip=[alt.Tooltip("Month:N", title=t("Month")), alt.Tooltip("Volume:Q", format=",.0f", title="m³"),
                 alt.Tooltip("Pump:Q", format=",.0f", title=t("Pump [kWh]"))])
    return bars.properties(height=300, title=t("Pumped groundwater per month"))


def drawdown_profile(d: Design, aquifer: dict) -> alt.Chart:
    """Water level along the line through a production and an injection well (peak flow)."""
    prod = [w for w in d.wells if w.q > 0][0]
    inj = [w for w in d.wells if w.q < 0][0]
    length = math.hypot(inj.x - prod.x, inj.y - prod.y)
    s_along = np.linspace(-length, 2 * length, 400)
    ux, uy = (inj.x - prod.x) / length, (inj.y - prod.y) / length
    xs = prod.x + s_along * ux
    ys = prod.y + s_along * uy
    from .hydraulics import head_change
    r_w = 0.2
    level = [aquifer["water_depth"] + head_change(d.wells, x, y, aquifer["kf"] * aquifer["thickness"], r_w)
             for x, y in zip(xs, ys)]
    data = pd.DataFrame({"Distance": s_along, "Level": level})
    line = alt.Chart(data).mark_line(color=WATER).encode(
        x=alt.X("Distance:Q", title=t("Distance from the production well [m]")),
        y=alt.Y("Level:Q", title=t("Water level below ground [m]"), scale=alt.Scale(reverse=True, zero=False)),
        tooltip=[alt.Tooltip("Distance:Q", format=".1f", title="m"),
                 alt.Tooltip("Level:Q", format=".2f", title=t("Level [m]"))])
    rest = alt.Chart(pd.DataFrame({"Level": [aquifer["water_depth"]]})).mark_rule(
        strokeDash=[6, 4], color=NEUTRAL).encode(y="Level:Q")
    return (line + rest).properties(height=300, title=t("Water level between the wells at peak flow (aquifer only)"))
