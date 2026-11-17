"""Colours and chart settings shared by every chart and drawing: the colours of supply and return, heating and
cooling, the series colours of the temperature charts and the chart style the results page lets you switch."""
from __future__ import annotations

from dataclasses import dataclass, fields

import altair as alt
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ghe_web import i18n
from ghe_web.inputs.load import MONTHS

alt.data_transformers.disable_max_rows()  # hourly charts have more than Altair's default 5000 rows

# One look for all Matplotlib drawings (inputs, layers, wells, site plan, PDF): the text and line colours of the page
# (look.PALETTE, light), titles at the left like the figure titles of the results, no box around the plots.
INK, INK_MUTED, INK_LIGHT, RULE = "#1e293b", "#475569", "#64748b", "#cbd5e1"
plt.rcParams.update({
    "font.size": 9, "text.color": INK, "axes.labelcolor": INK_MUTED, "axes.labelsize": 9,
    "axes.titlesize": 10.5, "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.titlepad": 8,
    "axes.titlecolor": INK, "axes.edgecolor": RULE, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK_LIGHT, "ytick.color": INK_LIGHT, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "xtick.major.size": 3, "ytick.major.size": 3, "xtick.major.width": 0.8, "ytick.major.width": 0.8,
    "grid.color": "#e2e8f0", "grid.linewidth": 0.8, "grid.alpha": 1.0,
    "legend.frameon": False, "legend.fontsize": 8.5,
    "figure.facecolor": "white", "savefig.facecolor": "white",
})


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


def load_colors(heating: str, cooling: str) -> alt.Scale:
    return alt.Scale(domain=[heating, cooling], range=[HEATING, COOLING])


def month_order() -> list[str]:
    """Month names in the current language, in calendar order (for sorting chart axes)."""
    return list(i18n.months())


def month_names(values) -> list[str]:
    """English month abbreviations (as in the result tables) in the current language."""
    names = dict(zip(MONTHS, i18n.months()))
    return [names.get(v, v) for v in values]


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
