"""Charts for inputs and results. No Streamlit code here, so they can be tested on their own.

Input charts are looked up per (section, variant) in DRAWINGS, so a new variant
(e.g. a coaxial pipe) only needs a new entry to get its own picture.
"""
from __future__ import annotations

from typing import Callable

import altair as alt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from .properties import SectionInput  # noqa: E402
from .properties.load import MONTHS  # noqa: E402

alt.data_transformers.disable_max_rows()  # hourly charts have more than Altair's default 5000 rows

GROUT = "#c9c4b8"
GROUND = "#e8e2d0"
PIPE_DOWN = "#d1495b"  # supply
PIPE_UP = "#2e86ab"  # return
# Loads: heating / extraction red, cooling / injection blue, in every chart. (Temperatures use blue for cold.)
HEATING = PIPE_DOWN
COOLING = PIPE_UP


def _load_colors(heating: str, cooling: str) -> alt.Scale:
    return alt.Scale(domain=[heating, cooling], range=[HEATING, COOLING])


# ---------------------------------------------------------------- inputs

def rectangular_layout(values: dict) -> plt.Figure:
    xs = [i * values["B_1"] for i in range(values["N_1"]) for _ in range(values["N_2"])]
    ys = [j * values["B_2"] for _ in range(values["N_1"]) for j in range(values["N_2"])]
    return borefield_layout(xs, ys, f"{len(xs)} boreholes, {values['B_1']} m × {values['B_2']} m spacing")


def custom_layout(values: dict) -> plt.Figure:
    from .geometry import closest_pair
    xs = [p[0] for p in values["points"]]
    ys = [p[1] for p in values["points"]]
    pair = closest_pair(values["points"])
    title = f"{len(xs)} boreholes" + (f", closest {pair[0]:.1f} m apart" if pair else "")
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
    ax.set_title(f"Borehole Ø {2 * r_b_mm:.0f} mm, outer pipe Ø {2 * values['r_out_out_mm']:.0f} mm", fontsize=10)
    ax.legend(handles=[Circle((0, 0), 1, color=PIPE_DOWN, label="Fluid going down (inner)"),
                       Circle((0, 0), 1, color=PIPE_UP, label="Fluid going up (annulus)")],
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
    ax.set_title(f"Borehole Ø {2 * r_b_mm:.0f} mm, pipe Ø {2 * values['r_out_mm']:.0f} mm", fontsize=10)
    ax.legend(handles=[Circle((0, 0), 1, color=PIPE_DOWN, label="Fluid going down"),
                       Circle((0, 0), 1, color=PIPE_UP, label="Fluid going up")],
              loc="lower center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=8)
    fig.tight_layout()
    return fig


def load_profile(values: dict) -> alt.Chart:
    """Monthly extracted and injected energy as bars."""
    data = pd.DataFrame({
        "Month": list(MONTHS) * 2,
        "Energy": [float(x) for x in values["baseload_extraction"]]
                  + [-float(x) for x in values["baseload_injection"]],
        "Type": ["Extraction (heating)"] * 12 + ["Injection (cooling)"] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title="Energy [kWh]"),
        color=alt.Color("Type:N", scale=_load_colors("Extraction (heating)", "Injection (cooling)"),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Month", "Type", alt.Tooltip("Energy:Q", format=",.0f")],
    ).properties(height=300, title="Monthly ground load")


def annual_demand_chart(values: dict) -> alt.Chart:
    from .properties.load import _annual_to_monthly
    heat, cool, heat_peak, cool_peak = _annual_to_monthly(values)
    data = pd.DataFrame({
        "Month": list(MONTHS) * 2,
        "Energy": [h / 1000 for h in heat] + [-c / 1000 for c in cool],
        "Peak": heat_peak + [-c for c in cool_peak],
        "Type": ["Heating demand"] * 12 + ["Cooling demand"] * 12,
    })
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title="Building demand [MWh]"),
        color=alt.Color("Type:N", scale=_load_colors("Heating demand", "Cooling demand"),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Month", "Type", alt.Tooltip("Energy:Q", format=",.1f", title="MWh"),
                 alt.Tooltip("Peak:Q", format=",.0f", title="Peak kW")],
    ).properties(height=280, title="Building demand per month (before heat pump efficiency)")


def hourly_demand(values: dict) -> tuple[alt.Chart, alt.Chart]:
    """Daily peak demand over the year next to the load duration curve."""
    prof = values["profile"]
    hourly = pd.DataFrame({"Heating": prof["heating"], "Cooling": prof["cooling"]})
    daily = hourly.groupby(hourly.index // 24).max()
    daily.index = pd.Index(range(1, len(daily) + 1), name="Day")
    data = daily.reset_index().melt("Day", var_name="Type", value_name="Power")
    colors = _load_colors("Heating", "Cooling")
    over_year = alt.Chart(data).mark_line(strokeWidth=1).encode(
        x=alt.X("Day:Q", title="Day of the year", scale=alt.Scale(domain=[1, 365])),
        y=alt.Y("Power:Q", title="Daily peak demand [kW]"),
        color=alt.Color("Type:N", scale=colors, legend=alt.Legend(orient="top", title=None)),
        tooltip=["Day", "Type", alt.Tooltip("Power:Q", format=".1f", title="kW")],
    ).properties(height=260, title="Daily peak demand")
    # Load duration curve: hours sorted from highest to lowest demand (every 10th hour is enough to draw it)
    duration = pd.concat([
        pd.DataFrame({"Hours": range(1, len(hourly) + 1), "Power": sorted(hourly[c], reverse=True), "Type": c})
        .iloc[::10] for c in ("Heating", "Cooling")])
    curve = alt.Chart(duration).mark_line().encode(
        x=alt.X("Hours:Q", title="Hours per year", scale=alt.Scale(domain=[0, 8760])),
        y=alt.Y("Power:Q", title="Demand [kW]"),
        color=alt.Color("Type:N", scale=colors, legend=alt.Legend(orient="top", title=None)),
        tooltip=["Type", "Hours", alt.Tooltip("Power:Q", format=".1f", title="kW")],
    ).properties(height=260, title="Load duration curve")
    return over_year, curve


def efficiency_curves(values: dict, operating: tuple[float, float] | None = None) -> tuple[alt.Chart, alt.Chart]:
    """COP (heating) and EER (cooling) against the average fluid temperature, as two charts so a high passive
    cooling EER does not flatten the COP curve. Optionally shades the fluid temperatures the design reaches."""
    from .properties.heat_pump import COP_TEMPS, EER_TEMPS, curves
    cop, eer = curves(values)
    charts = []
    for temps, vals, name, color in ((COP_TEMPS, cop, "COP heating", PIPE_DOWN), (EER_TEMPS, eer, "EER cooling", PIPE_UP)):
        data = pd.DataFrame({"T": temps, "Value": vals})
        line = alt.Chart(data).mark_line(point={"color": color}, color=color).encode(
            x=alt.X("T:Q", title="Average fluid temperature [°C]"),
            y=alt.Y("Value:Q", title=name, scale=alt.Scale(zero=False, padding=10), axis=alt.Axis(format=".1f")),
            tooltip=[alt.Tooltip("T:Q", title="°C"), alt.Tooltip("Value:Q", format=".2f", title=name)])
        title = name
        if operating is not None:
            band = alt.Chart(pd.DataFrame({"lo": [operating[0]], "hi": [operating[1]]})).mark_rect(
                opacity=0.15, color="#555").encode(x="lo:Q", x2="hi:Q")
            line = band + line
            title = f"{name} (grey: fluid temperatures of this design, {operating[0]:.1f} to {operating[1]:.1f} °C)"
        charts.append(line.properties(height=220, title=title))
    return tuple(charts)


def heat_pump_yearly_chart(table: pd.DataFrame, show_spf: bool) -> alt.Chart | tuple:
    """Electricity per year, and the seasonal performance factor per year when it changes."""
    cols = {"Electricity heating [MWh]": "Heating", "Electricity cooling [MWh]": "Cooling",
            "Electricity hot water [MWh]": "Hot water"}
    data = table[["Year", *cols]].rename(columns=cols).melt("Year", var_name="Use", value_name="MWh")
    data = data[data["MWh"] > 0]
    bars = alt.Chart(data).mark_bar().encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("MWh:Q", title="Electricity [MWh/yr]", stack=True),
        color=alt.Color("Use:N", scale=alt.Scale(domain=list(cols.values()), range=[PIPE_DOWN, PIPE_UP, "#e0a030"]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Year", "Use", alt.Tooltip("MWh:Q", format=",.1f")],
    ).properties(height=260, title="Heat pump electricity per year")
    if not show_spf:
        return bars
    spf = alt.Chart(table.dropna(subset=["SPF heating"])).mark_line(point={"color": PIPE_DOWN}, color=PIPE_DOWN).encode(
        x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("SPF heating:Q", title="SPF heating [-]", scale=alt.Scale(zero=False)),
        tooltip=["Year", alt.Tooltip("SPF heating:Q", format=".2f")],
    ).properties(height=220, title="Seasonal performance factor per year (falls as the ground cools)")
    return bars, spf


# Which drawing belongs to which input. Each function gets all inputs, so it can
# combine sections (the borehole drawing needs the radius from "borefield").
DRAWINGS: dict[tuple[str, str], tuple[str, Callable[[dict[str, SectionInput]], object]]] = {
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
            out.append((title, draw(inputs)))
    return out


# ---------------------------------------------------------------- results

AVERAGE_COLUMNS = ["Borehole wall", "Average fluid (base load)", "Average fluid (peak extraction)",
                   "Average fluid (peak injection)"]

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
    return alt.Color("Series:N", scale=alt.Scale(domain=series, range=[SERIES_COLORS.get(s, "#555") for s in series]),
                     legend=alt.Legend(orient="top", title=None, columns=2, labelLimit=260))


def _limit_rules(limits: dict, field: str = "Temperature") -> alt.Chart:
    """Dashed lines at the temperature limits, labelled on the left."""
    bounds = pd.DataFrame({field: [limits["T_min"], limits["T_max"]],
                           "Label": [f"min. limit {limits['T_min']:g} °C", f"max. limit {limits['T_max']:g} °C"]})
    base = alt.Chart(bounds)
    rules = base.mark_rule(strokeDash=[6, 4], color="#666").encode(y=f"{field}:Q")
    text = base.mark_text(align="right", dx=-4, dy=-7, fontSize=11, color="#555").encode(
        y=f"{field}:Q", x=alt.value("width"), text="Label:N")
    return rules + text


def _extreme_marks(data: pd.DataFrame, x: str, x_type: str = "Q") -> alt.Chart:
    """Points and labels at the lowest and highest temperature of the chart."""
    lo = data.loc[data["Temperature"].idxmin()]
    hi = data.loc[data["Temperature"].idxmax()]
    marks = pd.DataFrame({x: [lo[x], hi[x]], "Temperature": [lo["Temperature"], hi["Temperature"]],
                          "Label": [f"{round(lo['Temperature'], 1) + 0.0:.1f} °C", f"{round(hi['Temperature'], 1) + 0.0:.1f} °C"],
                          "dy": [14, -10]})
    base = alt.Chart(marks).encode(x=f"{x}:{x_type}", y="Temperature:Q")
    return base.mark_point(filled=True, size=60, color="black") + \
        base.mark_text(fontSize=11, fontWeight="bold", dy=14).encode(text="Label:N").transform_filter("datum.dy > 0") + \
        base.mark_text(fontSize=11, fontWeight="bold", dy=-10).encode(text="Label:N").transform_filter("datum.dy < 0")


def temperature_chart(temps: pd.DataFrame, limits: dict) -> alt.Chart:
    # Altair treats [ ] in field names specially, so units go in titles, not column names.
    data = temps[AVERAGE_COLUMNS].reset_index().melt("Years", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line(strokeWidth=1.6).encode(
        x=alt.X("Years:Q", title="Time [years]"),
        y=alt.Y("Temperature:Q", title="Temperature [°C]"),
        color=_series_color(AVERAGE_COLUMNS),
        tooltip=["Series", alt.Tooltip("Years:Q", format=".2f"), alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    extremes = data[data["Series"].isin(["Average fluid (peak extraction)", "Average fluid (peak injection)"])]
    return (lines + _limit_rules(limits) + _extreme_marks(extremes.reset_index(drop=True), "Years")).properties(
        height=380, title="Fluid temperatures over the simulation period")


def last_year_chart(temps: pd.DataFrame, limits: dict) -> alt.Chart:
    """Zoom on the last simulated year, with supply and return temperatures when they are known."""
    last = temps.tail(12).copy()
    if "Into borefield (peak extraction)" in last:
        last = last.drop(columns=["Borehole wall", "Average fluid (base load)"])
    last.index = pd.Index(list(MONTHS), name="Month")
    data = last.reset_index().melt("Month", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Temperature:Q", title="Temperature [°C]"),
        color=_series_color(list(last.columns)),
        tooltip=["Month", "Series", alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    return (lines + _limit_rules(limits)).properties(height=340, title="Last year of the simulation")


def hourly_band_chart(hourly: pd.DataFrame, limits: dict) -> alt.Chart:
    """Daily min-max band of the hourly fluid temperature over the whole simulation."""
    days = hourly["Average fluid"].groupby((hourly.index - 1) // 24).agg(["min", "max"])
    days["Years"] = ((days.index + 1) / 365).round(4)
    band = alt.Chart(days.round(2)).mark_area(opacity=0.5, color=PIPE_UP).encode(
        x=alt.X("Years:Q", title="Time [years]"),
        y=alt.Y("min:Q", title="Average fluid temperature [°C]"),
        y2="max:Q",
        tooltip=[alt.Tooltip("Years:Q", format=".2f"), alt.Tooltip("min:Q", format=".2f", title="Daily min °C"),
                 alt.Tooltip("max:Q", format=".2f", title="Daily max °C")],
    )
    return (band + _limit_rules(limits)).properties(height=380, title="Hourly fluid temperature (daily range)")


def hourly_last_year_chart(hourly: pd.DataFrame, limits: dict) -> alt.Chart:
    """The last simulated year: the fluid as a 3-hour min-max band (keeps every peak, a third of the points)
    and the borehole wall as a line."""
    last = hourly.tail(8760).reset_index(drop=True)
    agg = last.groupby(last.index // 3).agg(["min", "max", "mean"])
    data = pd.DataFrame({"Day": ((agg.index.to_numpy() * 3 + 1.5) / 24).round(3),
                         "min": agg[("Average fluid", "min")].round(2).to_numpy(),
                         "max": agg[("Average fluid", "max")].round(2).to_numpy(),
                         "Wall": agg[("Borehole wall", "mean")].round(2).to_numpy()})
    x = alt.X("Day:Q", title="Day of the last year", scale=alt.Scale(domain=[0, 365], nice=False))
    band = alt.Chart(data).mark_area(opacity=0.8, color=PIPE_UP).encode(
        x=x, y=alt.Y("min:Q", title="Temperature [°C]"), y2="max:Q",
        tooltip=[alt.Tooltip("Day:Q", format=".1f"), alt.Tooltip("min:Q", title="Fluid min °C"),
                 alt.Tooltip("max:Q", title="Fluid max °C")])
    wall = alt.Chart(data).mark_line(strokeWidth=1.2, color=SERIES_COLORS["Borehole wall"]).encode(x=x, y="Wall:Q")
    return (band + wall + _limit_rules(limits)).properties(
        height=380, title="Hourly temperatures in the last year (band: fluid, line: borehole wall)")


# ---------------------------------------------------------------- post-processing

def yearly_extremes_chart(df: pd.DataFrame, limits: dict) -> alt.Chart:
    data = df.melt("Year", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Year:O", title="Year", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Temperature:Q", title="Average fluid temperature [°C]"),
        color=_series_color(["Lowest", "Highest"]),
        tooltip=["Year", "Series", alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    return (lines + _limit_rules(limits)).properties(height=320, title="Lowest and highest temperature per year")


def energy_balance_chart(df: pd.DataFrame) -> alt.Chart:
    data = pd.DataFrame({"Month": list(df["Month"]) * 2,
                         "Energy": list(df["Extraction"]) + [-x for x in df["Injection"]],
                         "Type": ["Extraction (from ground)"] * 12 + ["Injection (into ground)"] * 12})
    imbalance = df["Injection"].sum() - df["Extraction"].sum()
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title="Ground energy [MWh]"),
        color=alt.Color("Type:N", scale=_load_colors("Extraction (from ground)", "Injection (into ground)"),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Month", "Type", alt.Tooltip("Energy:Q", format=",.1f", title="MWh")],
    ).properties(height=320, title=f"Ground energy balance (yearly imbalance {imbalance:+,.0f} MWh)")


def heatmap_chart(hourly: pd.DataFrame) -> alt.Chart:
    """Average fluid temperature in the last year: day of the year against hour of the day."""
    last = hourly["Average fluid"].tail(8760).to_numpy()
    data = pd.DataFrame({"Day": [h // 24 + 1 for h in range(8760)], "Hour": [h % 24 for h in range(8760)],
                         "Temperature": last})
    return alt.Chart(data).mark_rect().encode(
        x=alt.X("Day:O", title="Day of the last year", axis=alt.Axis(values=list(range(1, 366, 30)), labelAngle=0)),
        y=alt.Y("Hour:O", title="Hour of the day", axis=alt.Axis(values=[0, 6, 12, 18])),
        color=alt.Color("Temperature:Q", scale=alt.Scale(scheme="redyellowblue", reverse=True),
                        title="°C"),
        tooltip=["Day", "Hour", alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    ).properties(height=300, title="When it gets cold or warm (average fluid temperature, last year)")


def tornado_chart(df: pd.DataFrame) -> alt.Chart:
    base = float(df["Base"].iloc[0])
    rows = []
    for _, r in df.iterrows():
        # in percent, so the chart also reads right when the result itself was sized hourly
        rows.append({"Input": r["Input"], "Case": "Lower input", "Delta": (r["Low"] / base - 1) * 100,
                     "Length": r["Low"]})
        rows.append({"Input": r["Input"], "Case": "Higher input", "Delta": (r["High"] / base - 1) * 100,
                     "Length": r["High"]})
    data = pd.DataFrame(rows)
    return alt.Chart(data).mark_bar().encode(
        y=alt.Y("Input:N", sort=list(df["Input"]), title=None, axis=alt.Axis(labelLimit=260)),
        yOffset=alt.YOffset("Case:N"),
        x=alt.X("Delta:Q", title="Change in borehole length [%]"),
        color=alt.Color("Case:N", scale=alt.Scale(domain=["Lower input", "Higher input"], range=[PIPE_UP, PIPE_DOWN]),
                        legend=alt.Legend(orient="top", title=None)),
        tooltip=["Input", "Case", alt.Tooltip("Length:Q", format=".1f", title="Length m"),
                 alt.Tooltip("Delta:Q", format="+.1f", title="Change %")],
    ).properties(height=alt.Step(18), title="What the borehole length depends on most")


def comparison_chart(df: pd.DataFrame, column: str, title: str) -> alt.Chart:
    # Altair cannot use field names with brackets, so the column is copied to a plain name
    data = pd.DataFrame({"Variant": df["Variant"], "Value": df[column]})
    return alt.Chart(data).mark_bar(color=PIPE_UP).encode(
        x=alt.X("Value:Q", title=title),
        y=alt.Y("Variant:N", sort=None, title=None, axis=alt.Axis(labelLimit=200)),
        tooltip=["Variant", alt.Tooltip("Value:Q", format=",.1f", title=title)],
    ).properties(height=alt.Step(28))


def gfunction_chart(df: pd.DataFrame) -> alt.Chart:
    return alt.Chart(df).mark_line(color=PIPE_UP).encode(
        x=alt.X("ln_t_ts:Q", title="ln(t/ts)"),
        y=alt.Y("g:Q", title="g-function"),
        tooltip=[alt.Tooltip("hours:Q", format=",.0f", title="Time h"), alt.Tooltip("g:Q", format=".3f",
                                                                                    title="g-function")],
    ).properties(height=300, title="g-function of the borefield (thermal interaction of the boreholes)")


def load_duration_chart(df: pd.DataFrame) -> alt.Chart:
    """Building demand and ground load, each sorted from the highest hour to the lowest."""
    cols = [c for c in df.columns if c != "Hours"]
    data = df.iloc[::10].melt("Hours", value_vars=cols, var_name="Load", value_name="Power")
    colors = {"Heating demand": HEATING, "Cooling demand": COOLING, "Ground extraction": "#f2a3ad",
              "Ground injection": "#95c4d9"}
    dashes = {"Ground extraction": [5, 3], "Ground injection": [5, 3]}
    return alt.Chart(data).mark_line().encode(
        x=alt.X("Hours:Q", title="Hours per year", scale=alt.Scale(domain=[0, 8760])),
        y=alt.Y("Power:Q", title="Power [kW]"),
        color=alt.Color("Load:N", scale=alt.Scale(domain=cols, range=[colors.get(c, "#555") for c in cols]),
                        legend=alt.Legend(orient="top", title=None)),
        strokeDash=alt.StrokeDash("Load:N", scale=alt.Scale(domain=cols, range=[dashes.get(c, [1, 0]) for c in cols]),
                                  legend=None),
        tooltip=["Load", "Hours", alt.Tooltip("Power:Q", format=",.1f", title="kW")],
    ).properties(height=300, title="Load duration curve (first year)")


def pressure_drop_chart(df: pd.DataFrame, flow: float, dp: float) -> alt.Chart:
    data = pd.DataFrame({"Flow": df["Flow per borehole [l/s]"], "Drop": df["Pressure drop [kPa]"]})
    line = alt.Chart(data).mark_line(color=PIPE_UP).encode(
        x=alt.X("Flow:Q", title="Flow rate per borehole [l/s]"),
        y=alt.Y("Drop:Q", title="Pressure drop per borehole [kPa]"),
        tooltip=[alt.Tooltip("Flow:Q", format=".3f", title="l/s"), alt.Tooltip("Drop:Q", format=".1f", title="kPa")])
    point = pd.DataFrame({"Flow": [flow], "Drop": [dp], "Label": [f"design: {dp:.1f} kPa"]})
    base = alt.Chart(point).encode(x="Flow:Q", y="Drop:Q")
    return (line + base.mark_point(filled=True, size=80, color="black")
            + base.mark_text(align="left", dx=8, dy=-8, fontWeight="bold").encode(text="Label:N")).properties(
        height=300, title="Pressure drop against flow rate")


def ground_map_chart(m: dict) -> alt.Chart:
    """Ground temperature at mid-depth around the field at the end of the simulation."""
    table, holes = m["table"], m["boreholes"]
    lim = max(m["max_change"], 0.1)
    cell = m["cell"]
    heat = alt.Chart(table.assign(x2=table["x"] + cell, y2=table["y"] + cell)).mark_rect().encode(
        x=alt.X("x:Q", title="x [m]", scale=alt.Scale(nice=False)), x2="x2:Q",
        y=alt.Y("y:Q", title="y [m]", scale=alt.Scale(nice=False)), y2="y2:Q",
        color=alt.Color("Change:Q", title="Change [K]", scale=alt.Scale(scheme="redblue", reverse=True,
                                                                         domain=[-lim, lim])),
        tooltip=[alt.Tooltip("x:Q", format=".0f"), alt.Tooltip("y:Q", format=".0f"),
                 alt.Tooltip("Change:Q", format="+.2f", title="Change K"),
                 alt.Tooltip("Temperature:Q", format=".2f", title="Ground °C")])
    dots = alt.Chart(holes).mark_point(shape="circle", size=12, color="black", filled=True).encode(x="x:Q", y="y:Q")
    return (heat + dots).properties(height=440, width=440,
                                    title=f"Ground temperature change at {m['depth']:.0f} m depth after "
                                          f"{m['years']} years")


def optimisation_chart(monthly: pd.DataFrame) -> alt.Chart:
    """Average monthly building demand split into the part the ground covers and the external part."""
    rows = []
    for _, r in monthly.iterrows():
        for kind, sign in (("heating", 1), ("cooling", -1)):
            rows.append({"Month": r["Month"], "Part": f"Ground {kind}", "Energy": sign * r[f"Ground {kind} [MWh]"]})
            rows.append({"Month": r["Month"], "Part": f"Backup {kind}", "Energy": sign * r[f"External {kind} [MWh]"]})
    data = pd.DataFrame(rows)
    parts = ["Ground heating", "Backup heating", "Ground cooling", "Backup cooling"]
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Energy:Q", title="Building demand [MWh] (cooling below zero)"),
        color=alt.Color("Part:N", scale=alt.Scale(domain=parts, range=[HEATING, "#f2c4ca", COOLING, "#bcdbe8"]),
                        legend=alt.Legend(orient="top", title=None)),
        order=alt.Order("Part:N"),
        tooltip=["Month", "Part", alt.Tooltip("Energy:Q", format=",.1f", title="MWh")],
    ).properties(height=320, title="Who covers the demand (average year)")
