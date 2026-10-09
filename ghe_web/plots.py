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
import pandas as pd  # noqa: E402
from matplotlib.patches import Circle  # noqa: E402

from .properties import SectionInput  # noqa: E402
from .properties.load import MONTHS  # noqa: E402

GROUT = "#c9c4b8"
GROUND = "#e8e2d0"
PIPE_DOWN = "#d1495b"  # supply
PIPE_UP = "#2e86ab"  # return


# ---------------------------------------------------------------- inputs

def borefield_layout(values: dict) -> plt.Figure:
    """Top view of a rectangular borefield."""
    xs = [i * values["B_1"] for i in range(values["N_1"]) for _ in range(values["N_2"])]
    ys = [j * values["B_2"] for _ in range(values["N_1"]) for j in range(values["N_2"])]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(xs, ys, s=40, color=PIPE_UP, zorder=3)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(f"{len(xs)} boreholes, {values['B_1']} m × {values['B_2']} m spacing", fontsize=10)
    ax.grid(alpha=0.3)
    ax.margins(0.08)
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
        color=alt.Color("Type:N", scale=alt.Scale(range=[PIPE_DOWN, PIPE_UP]),
                        legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Month", "Type", alt.Tooltip("Energy:Q", format=",.0f")],
    ).properties(height=300, title="Monthly ground load")


# Which drawing belongs to which input. Each function gets all inputs, so it can
# combine sections (the borehole drawing needs the radius from "borefield").
DRAWINGS: dict[tuple[str, str], tuple[str, Callable[[dict[str, SectionInput]], object]]] = {
    ("borefield", "rectangular"): ("Borefield layout", lambda i: borefield_layout(i["borefield"].values)),
    ("pipe", "single_u"): ("Borehole cross-section",
                           lambda i: _u_tube_cross_section(i["pipe"].values, i["borefield"].values["r_b_mm"], 2)),
    ("pipe", "double_u"): ("Borehole cross-section",
                           lambda i: _u_tube_cross_section(i["pipe"].values, i["borefield"].values["r_b_mm"], 4)),
    ("load", "monthly"): ("Ground load", lambda i: load_profile(i["load"].values)),
}


def input_drawings(inputs: dict[str, SectionInput]) -> list[tuple[str, object]]:
    """All drawings available for the current inputs, as (title, figure or chart)."""
    out = []
    for (section, variant), (title, draw) in DRAWINGS.items():
        if section in inputs and inputs[section].variant == variant:
            out.append((title, draw(inputs)))
    return out


# ---------------------------------------------------------------- results

def temperature_chart(temps: pd.DataFrame, limits: dict) -> alt.Chart:
    # Altair treats [ ] in field names specially, so units go in titles, not column names.
    data = temps.reset_index().melt("Years", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line().encode(
        x=alt.X("Years:Q", title="Time [years]"),
        y=alt.Y("Temperature:Q", title="Temperature [°C]"),
        color=alt.Color("Series:N", legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Series", alt.Tooltip("Years:Q", format=".2f"), alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    bounds = pd.DataFrame({"Temperature": [limits["T_min"], limits["T_max"]]})
    rules = alt.Chart(bounds).mark_rule(strokeDash=[6, 4], color="gray").encode(y="Temperature:Q")
    return (lines + rules).properties(height=380, title="Fluid temperatures over the simulation period")


def last_year_chart(temps: pd.DataFrame, limits: dict) -> alt.Chart:
    """Zoom on the last simulated year, where temperatures are usually most extreme."""
    last = temps.tail(12).copy()
    last.index = pd.Index(list(MONTHS), name="Month")
    data = last.reset_index().melt("Month", var_name="Series", value_name="Temperature")
    lines = alt.Chart(data).mark_line(point=True).encode(
        x=alt.X("Month:N", sort=list(MONTHS), title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Temperature:Q", title="Temperature [°C]"),
        color=alt.Color("Series:N", legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Month", "Series", alt.Tooltip("Temperature:Q", format=".2f", title="°C")],
    )
    bounds = pd.DataFrame({"Temperature": [limits["T_min"], limits["T_max"]]})
    rules = alt.Chart(bounds).mark_rule(strokeDash=[6, 4], color="gray").encode(y="Temperature:Q")
    return (lines + rules).properties(height=320, title="Last year of the simulation")
