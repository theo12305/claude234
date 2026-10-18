"""Results export: an Excel workbook with every table, and a zip with workbook, PDF report and project file."""
from __future__ import annotations

import io
import zipfile

import pandas as pd

from . import analysis, i18n, model, properties, report
from .i18n import fmt, t
from .properties import SectionInput
from .report import METHOD


def summary_table(result: model.SizingResult, inputs: dict[str, SectionInput], name: str = "") -> pd.DataFrame:
    key = analysis.key_results(result, inputs)
    project, field = t("Project"), t("Borefield")
    rows = [(project, t("Name"), name.strip() or "-", ""),
            (project, t("Date"), report._today(), ""),
            (project, t("Calculation"), t(METHOD[result.sizing_method]), ""),
            (field, t("Borehole length"), fmt("{x:.1f} m", x=result.borehole_length), ""),
            (field, t("Number of boreholes"), str(result.number_of_boreholes), ""),
            (field, t("Total borehole length"), fmt("{x:,.0f} m", x=result.total_length), "")]
    rows += [(group, label, value, note) for group, (label, value, note) in zip(key.groups, key.rows)]
    rows += [(t("Warning"), "", w, "") for w in key.warnings]
    return pd.DataFrame(rows, columns=[t("Group"), t("Item"), t("Value"), t("Note")])


def inputs_table(inputs: dict[str, SectionInput]) -> pd.DataFrame:
    """One row per scalar input. Tables (monthly loads, positions, hourly profiles) get their own sheets."""
    rows = []
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        label = t(section.label)
        rows.append((label, t("Type"), t(variant.label), ""))
        for p in variant.properties:
            if p.kind in ("monthly", "points", "hourly"):
                continue
            if p.kind == "layers":
                layers = chosen.values.get(p.key) or {}
                rows.append((label, t(p.label), t("{n} layers, used in the calculation", n=len(layers.get("rows") or ()))
                             if layers.get("use") else t("{n} layers, not used", n=len(layers.get("rows") or ())), ""))
                continue
            value = chosen.values.get(p.key)
            if isinstance(value, bool):
                value = t("yes") if value else t("no")
            elif isinstance(value, str):
                value = t(value)
            rows.append((label, t(p.label), value, t(p.unit)))
    return pd.DataFrame(rows, columns=[t("Section"), t("Input"), t("Value"), t("Unit")])


def _table_inputs(inputs: dict[str, SectionInput]) -> dict[str, pd.DataFrame]:
    sheets = {}
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        monthly = {f"{t(p.label)} [{p.unit}]": chosen.values[p.key] for p in variant.properties if p.kind == "monthly"}
        if monthly:
            sheets[t("Input {section}", section=t(section.label))[:31]] = pd.DataFrame(
                monthly, index=pd.Index(i18n.months(), name=t("Month")))
        for p in variant.properties:
            if p.kind == "points":
                sheets[t("Input borehole positions")[:31]] = pd.DataFrame(
                    list(chosen.values[p.key]), columns=["x [m]", "y [m]"],
                    index=pd.RangeIndex(1, len(chosen.values[p.key]) + 1, name=t("Borehole")))
            elif p.kind == "layers" and (chosen.values[p.key] or {}).get("rows"):
                sheets[t("Input ground layers")[:31]] = layer_table(chosen.values[p.key]["rows"])
            elif p.kind == "hourly":
                prof = chosen.values[p.key]
                sheets[t("Input hourly demand")[:31]] = pd.DataFrame(
                    {t("Heating [kW]"): prof["heating"], t("Cooling [kW]"): prof["cooling"]},
                    index=pd.RangeIndex(1, len(prof["heating"]) + 1, name=t("Hour")))
    return sheets


def layer_table(rows) -> pd.DataFrame:
    return pd.DataFrame([{t("From [m]"): r["top"], t("To [m]"): r["bottom"], t("Rock"): t(r.get("rock", "")),
                          t("Thermal conductivity [W/(m·K)]"): r["k_s"],
                          t("Volumetric heat capacity [MJ/(m³·K)]"): r["C"],
                          t("Confidence"): r.get("confidence"), t("Basis"): basis(r.get("basis", ""))} for r in rows],
                        index=pd.RangeIndex(1, len(rows) + 1, name=t("Layer")))


def basis(text: str) -> str:
    """Where a layer comes from ("4 logs, above groundwater"), in the current language."""
    from .strata.predict import describe_basis
    return describe_basis(text)


def monthly_temperatures(result: model.SizingResult) -> pd.DataFrame:
    table = result.temperatures.reset_index(drop=True)
    names = [c for c in table.columns]
    table.insert(0, t("Month"), [i18n.month(i % 12) for i in range(len(table))])
    table.insert(0, t("Year"), [i // 12 + 1 for i in range(len(table))])
    return table.rename(columns={c: f"{t(c)} [°C]" for c in names})


def excel_workbook(result: model.SizingResult, inputs: dict[str, SectionInput], name: str = "",
                   extra: dict[str, pd.DataFrame] | None = None) -> bytes:
    """All results in one workbook: summary, inputs, monthly/yearly/hourly tables and any extra analysis."""
    sheets: dict[str, tuple[pd.DataFrame, bool]] = {  # name: (table, write the index)
        t("Summary"): (summary_table(result, inputs, name), False),
        t("Inputs"): (inputs_table(inputs), False),
    }
    sheets.update({k: (v, True) for k, v in _table_inputs(inputs).items()})
    sheets[t("Monthly temperatures")[:31]] = (monthly_temperatures(result), False)
    extremes = analysis.yearly_extremes(result).rename(columns={
        "Year": t("Year"), "Lowest": t("Lowest [°C]"), "Highest": t("Highest [°C]")})
    sheets[t("Yearly min-max")[:31]] = (extremes, False)
    energy = analysis.monthly_ground_energy(result)
    energy["Month"] = list(i18n.months())
    energy = energy.rename(columns={"Month": t("Month"), "Extraction": t("Extraction [MWh]"),
                                    "Injection": t("Injection [MWh]")})
    sheets[t("Ground energy")[:31]] = (energy, False)
    if result.heat_pump is not None:
        sheets[t("Heat pump")[:31]] = (result.heat_pump.round(3).rename(columns=t), False)
    if result.hourly_temperatures is not None:
        hourly = result.hourly_temperatures.round(3).rename(columns=lambda c: f"{t(c)} [°C]")
        hourly.index.name = t("Hour")
        sheets[t("Hourly temperatures")[:31]] = (hourly, True)
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
               extra: dict[str, pd.DataFrame] | None = None, report_options: report.ReportOptions | None = None,
               report_extras: dict | None = None) -> bytes:
    """Workbook, PDF report and the project file, so a design can be archived or shared in one file."""
    stem = name.strip() or "ghetool-project"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{stem}.xlsx", excel_workbook(result, inputs, name, extra))
        z.writestr(f"{stem}.pdf", report.make_pdf(result, inputs, name, report_options, report_extras))
        z.writestr(f"{stem}.json", model.to_json(inputs, name))
    return buf.getvalue()
