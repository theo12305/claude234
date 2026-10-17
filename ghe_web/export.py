"""Results export: an Excel workbook with every table, and a zip with workbook, PDF report and project file."""
from __future__ import annotations

import datetime as dt
import io
import zipfile

import pandas as pd

from . import analysis, model, properties, report
from .properties import SectionInput
from .properties.load import MONTHS

METHOD = {"check": "Check of a given length", "hourly": "Sizing, hourly (L4)", "monthly": "Sizing, monthly (L2/L3)"}


def summary_table(result: model.SizingResult, inputs: dict[str, SectionInput], name: str = "") -> pd.DataFrame:
    key = analysis.key_results(result, inputs)
    rows = [("Project", "Name", name.strip() or "-", ""),
            ("Project", "Date", dt.date.today().isoformat(), ""),
            ("Project", "Calculation", METHOD[result.sizing_method], ""),
            ("Borefield", "Borehole length", f"{result.borehole_length:.1f} m", ""),
            ("Borefield", "Number of boreholes", str(result.number_of_boreholes), ""),
            ("Borefield", "Total length", f"{result.total_length:,.0f} m", "")]
    rows += [(group, label, value, note) for group, (label, value, note) in zip(key.groups, key.rows)]
    rows += [("Warning", "", w, "") for w in key.warnings]
    return pd.DataFrame(rows, columns=["Group", "Item", "Value", "Note"])


def inputs_table(inputs: dict[str, SectionInput]) -> pd.DataFrame:
    """One row per scalar input. Tables (monthly loads, positions, hourly profiles) get their own sheets."""
    rows = []
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        rows.append((section.label, "Type", variant.label, ""))
        for p in variant.properties:
            if p.kind in ("monthly", "points", "hourly"):
                continue
            rows.append((section.label, p.label, chosen.values.get(p.key), p.unit))
    return pd.DataFrame(rows, columns=["Section", "Input", "Value", "Unit"])


def _table_inputs(inputs: dict[str, SectionInput]) -> dict[str, pd.DataFrame]:
    sheets = {}
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        monthly = {f"{p.label} [{p.unit}]": chosen.values[p.key] for p in variant.properties if p.kind == "monthly"}
        if monthly:
            sheets[f"Input {section.label}"[:31]] = pd.DataFrame(monthly, index=pd.Index(MONTHS, name="Month"))
        for p in variant.properties:
            if p.kind == "points":
                sheets["Input borehole positions"] = pd.DataFrame(
                    list(chosen.values[p.key]), columns=["x [m]", "y [m]"],
                    index=pd.RangeIndex(1, len(chosen.values[p.key]) + 1, name="Borehole"))
            elif p.kind == "hourly":
                prof = chosen.values[p.key]
                sheets["Input hourly demand"] = pd.DataFrame(
                    {"Heating [kW]": prof["heating"], "Cooling [kW]": prof["cooling"]},
                    index=pd.RangeIndex(1, len(prof["heating"]) + 1, name="Hour"))
    return sheets


def monthly_temperatures(result: model.SizingResult) -> pd.DataFrame:
    t = result.temperatures.reset_index(drop=True)
    t.insert(0, "Month", [MONTHS[i % 12] for i in range(len(t))])
    t.insert(0, "Year", [i // 12 + 1 for i in range(len(t))])
    return t.rename(columns={c: f"{c} [°C]" for c in t.columns if c not in ("Year", "Month")})


def excel_workbook(result: model.SizingResult, inputs: dict[str, SectionInput], name: str = "",
                   extra: dict[str, pd.DataFrame] | None = None) -> bytes:
    """All results in one workbook: summary, inputs, monthly/yearly/hourly tables and any extra analysis."""
    sheets: dict[str, tuple[pd.DataFrame, bool]] = {  # name: (table, write the index)
        "Summary": (summary_table(result, inputs, name), False),
        "Inputs": (inputs_table(inputs), False),
    }
    sheets.update({k: (v, True) for k, v in _table_inputs(inputs).items()})
    sheets["Monthly temperatures"] = (monthly_temperatures(result), False)
    extremes = analysis.yearly_extremes(result).rename(columns={"Lowest": "Lowest [°C]", "Highest": "Highest [°C]"})
    sheets["Yearly min-max"] = (extremes, False)
    energy = analysis.monthly_ground_energy(result).rename(columns={"Extraction": "Extraction [MWh]",
                                                                   "Injection": "Injection [MWh]"})
    sheets["Ground energy"] = (energy, False)
    if result.heat_pump is not None:
        sheets["Heat pump"] = (result.heat_pump.round(3), False)
    if result.hourly_temperatures is not None:
        sheets["Hourly temperatures"] = (result.hourly_temperatures.round(3).rename(
            columns=lambda c: f"{c} [°C]"), True)
    for title, table in (extra or {}).items():
        if table is not None and len(table):
            sheets[title[:31]] = (table, False)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for title, (table, index) in sheets.items():
            table.to_excel(writer, sheet_name=title, index=index)
            ws = writer.sheets[title]
            ws.freeze_panes = "A2"
            for col in ws.columns:  # rough auto width from the first 200 rows
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
    return buf.getvalue()


def zip_bundle(result: model.SizingResult, inputs: dict[str, SectionInput], name: str = "",
               extra: dict[str, pd.DataFrame] | None = None) -> bytes:
    """Workbook, PDF report and the project file, so a design can be archived or shared in one file."""
    stem = name.strip() or "ghetool-project"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.xlsx", excel_workbook(result, inputs, name, extra))
        z.writestr(f"{stem}.pdf", report.make_pdf(result, inputs, name))
        z.writestr(f"{stem}.json", model.to_json(inputs, name))
    return buf.getvalue()
