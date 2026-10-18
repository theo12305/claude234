"""Hourly heating and cooling demand: reading files and a built-in example profile."""
from __future__ import annotations

import io
import math

import pandas as pd

from .i18n import t

HOURS = 8760


class HourlyFileError(ValueError):
    """A problem with the uploaded file, worded for the user."""


def read_profile(name: str, content: bytes) -> tuple[list[float], list[float], list[str]]:
    """Read heating and cooling demand [kW] for each hour of one year.

    CSV (comma, semicolon or tab separated, decimal point or comma) or Excel.
    The first two numeric columns are taken as heating and cooling. A header row is optional.
    Returns (heating, cooling, notes).
    """
    try:
        if name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content), header=None)
        else:
            text = content.decode("utf-8-sig", errors="replace")
            sep = max([";", "\t", ","], key=lambda s: text.splitlines()[0].count(s) if text else 0)
            decimal = "," if sep != "," and _uses_decimal_comma(text) else "."
            df = pd.read_csv(io.StringIO(text), sep=sep, decimal=decimal, header=None, engine="python")
    except Exception as exc:
        raise HourlyFileError(t("Could not read {name}: {error}", name=name, error=exc)) from exc

    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna(axis=1, how="all")
    if df.shape[1] < 2:
        raise HourlyFileError(t("The file needs two columns with numbers: heating and cooling demand in kW."))
    df = df.iloc[:, :2].dropna(how="all")  # drops a text header row
    notes = []
    if df.isna().any().any():
        notes.append(t("{n} empty cells were read as 0 kW.", n=int(df.isna().sum().sum())))
        df = df.fillna(0)
    if len(df) == HOURS + 24:
        notes.append(t("The file has 8784 hours (leap year); the last day was dropped."))
        df = df.iloc[:HOURS]
    if len(df) != HOURS:
        raise HourlyFileError(t("Expected {hours} hourly values (one year), found {n}.", hours=HOURS, n=len(df)))
    if (df < 0).any().any():
        raise HourlyFileError(t("The demand cannot be negative. Put heating and cooling in separate columns, both "
                                "positive."))
    heating, cooling = (df.iloc[:, i].astype(float).round(3).tolist() for i in (0, 1))
    return heating, cooling, notes


def _uses_decimal_comma(text: str) -> bool:
    sample = text[:5000]
    return sample.count(",") > 0 and sample.count(".") == 0


def example_profile() -> dict[str, list[float]]:
    """Synthetic office-like demand: heating below 15 °C outdoor, cooling above 18 °C, office hours."""
    heating, cooling = [], []
    for h in range(HOURS):
        day, hour = divmod(h, 24)
        t_out = 10 - 9 * math.cos(2 * math.pi * (day - 20) / 365) + 4 * math.sin(2 * math.pi * (hour - 9) / 24)
        office = 1.0 if (day % 7 < 5 and 7 <= hour < 19) else 0.4
        heating.append(round(max(0.0, 12 * (15 - t_out)) * office, 2))
        cooling.append(round(max(0.0, 14 * (t_out - 18)) * office, 2))
    return {"heating": heating, "cooling": cooling}
