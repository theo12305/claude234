"""Charts of the results: temperatures over the years, the last year, hourly temperatures, energy balance,
g-function, ground temperature map and the charts of the further analysis. No Streamlit code here.
"""
from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd

from ghe_web import i18n
from ghe_web.i18n import fmt, t
from ghe_web.charts.palette import (AVERAGE_COLUMNS, COOLING, ChartStyle, DEFAULT_STYLE, EXTRACTION,  # noqa: E402
                                    HEATING, INJECTION, NEUTRAL, PIPE_DOWN, PIPE_UP, SERIES_COLORS, month_names,
                                    month_order)


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
    last.index = pd.Index(month_order(), name="Month")
    data = _translate_series(last.reset_index().melt("Month", var_name="Series", value_name="Temperature"))
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Month:N", sort=month_order(), title=None, axis=alt.Axis(labelAngle=-90 if compact else 0)),
        y=alt.Y("Temperature:Q", title=t("Mean fluid temperature [°C]") if not compact else None,
                scale=alt.Scale(domain=domain, nice=False) if compact else alt.Undefined),
        color=_series_color(list(last.columns)) if not compact else
        alt.Color("Series:N", scale=alt.Scale(domain=[t(s) for s in last.columns],
                                              range=[SERIES_COLORS[s] for s in last.columns]), legend=None),
    )
    hover = _crosshair(last.reset_index(), "Month", "N", list(last.columns), x_title=t("Month"), sort=month_order()) \
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
    months = month_names(df["Month"])
    top = float(max(df["Extraction"].max(), df["Injection"].max(), 0.0))
    bars = pd.DataFrame({"Month": months * 2,
                         "Energy": [-float(x) for x in df["Extraction"]] + [float(x) for x in df["Injection"]],
                         "Type": [ext] * 12 + [inj] * 12})
    bars["Label"] = [_energy_text(abs(v), top) if abs(v) >= top * 0.005 and abs(v) > 0 else "" for v in bars["Energy"]]
    line = pd.DataFrame({"Month": months, "Energy": (df["Injection"] - df["Extraction"]).astype(float).to_list(),
                         "Type": [net] * 12})
    colour = alt.Color("Type:N", scale=alt.Scale(domain=[ext, inj, net], range=[EXTRACTION, INJECTION, NEUTRAL]),
                       legend=alt.Legend(orient="top", title=None, labelLimit=300, columns=1))
    x = alt.X("Month:N", sort=month_order(), title=None, axis=alt.Axis(labelAngle=0))
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
        month = month_names([r["Month"]])[0]
        for kind, sign in (("heating", 1), ("cooling", -1)):
            rows.append({"Month": month, "Part": t(f"Ground {kind}"), "Energy": sign * r[f"Ground {kind} [MWh]"]})
            rows.append({"Month": month, "Part": t(f"Backup {kind}"), "Energy": sign * r[f"External {kind} [MWh]"]})
    data = pd.DataFrame(rows)
    parts = [t("Ground heating"), t("Backup heating"), t("Ground cooling"), t("Backup cooling")]
    return alt.Chart(data).mark_bar().encode(
        x=alt.X("Month:N", sort=month_order(), title=None, axis=alt.Axis(labelAngle=0)),
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
