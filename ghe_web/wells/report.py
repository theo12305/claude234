"""Key results of a well design as rows, and the Excel workbook and PDF report. No Streamlit code here."""
from __future__ import annotations

import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from .. import i18n  # noqa: E402
from ..export import inputs_table  # noqa: E402
from ..i18n import fmt, t  # noqa: E402
from ..properties import SectionInput  # noqa: E402
from ..report import A4, _today  # noqa: E402
from . import checks, design, plots  # noqa: E402


def key_groups(d: design.Design, inputs: dict[str, SectionInput]) -> dict[str, list[tuple[str, str, str]]]:
    """The key results in groups of (item, value, note)."""
    years = int(d.temperatures["year"].max())
    return {
        t("Water"): [
            (t("Peak flow"), fmt("{a:.1f} m³/h · {b:.2f} l/s", a=d.q_peak * 3600, b=d.q_peak * 1000),
             t("{x:.1f} m³/h per production well", x=d.q_peak_well * 3600)),
            (t("Average flow while running"), fmt("{x:.1f} m³/h", x=d.q_operating * 3600),
             t("in the months with load")),
            (t("Water per year"), fmt("{x:,.0f} m³", x=d.volume_year), t("for the water right application")),
            (t("Largest daily volume"), fmt("{x:,.0f} m³/d", x=d.q_peak * 86400), t("peak flow for 24 h")),
        ],
        t("Wells"): [
            (t("Production / injection wells"), fmt("{a} / {b}", a=d.n_production, b=d.n_injection),
             t("sized") if d.mode == "size" else t("given")),
            (t("Distance between the wells"), fmt("{x:g} m", x=d.distance),
             t("no backflow from {x:.0f} m (injection downstream)", x=d.critical_distance)
             if d.critical_distance < 1e5 else t("no groundwater flow")),
            (t("Depth and screen"), fmt("{a:.1f} m · {b:.1f} m", a=d.screen.depth, b=d.screen.length),
             t("screen from {a:.1f} m", a=d.screen.top)),
            (t("Entrance velocity"), fmt("{x:.2f} mm/s", x=max(d.v_entrance_production, d.v_entrance_injection) * 1000),
             t("allowed {x:.2f} mm/s (Sichardt)", x=d.v_allowed * 1000)),
        ],
        t("Pump"): [
            (t("Total head"), fmt("{x:.1f} m", x=d.pump_head), t("lift + drawdown + pipe and heat exchanger losses")),
            (t("Electric power"), fmt("{x:,.0f} W", x=d.pump_power), t("all production pumps at peak flow")),
            (t("Pump energy"), fmt("{x:,.0f} kWh/yr", x=d.pump_energy_year), ""),
            *([(t("Seasonal performance factor"), fmt("{x:.2f}", x=d.spf),
                t("heat pump and well pumps together"))] if d.spf else []),
        ],
        t("Temperatures"): [
            (t("Natural groundwater"), fmt("{x:.1f} °C", x=d.t_groundwater), t("from Ground, at the screen")),
            (t("Injection"), fmt("{a:.1f} to {b:.1f} °C", a=d.t_injection_min, b=d.t_injection_max), ""),
            (t("Thermal breakthrough"), t("after {x:.1f} years", x=d.breakthrough_years)
             if d.breakthrough_years is not None else t("none in {n} years", n=years),
             t("change of the production temperature at most {x:.2f} K", x=d.drift)),
            (t("Plume ({k:g} K)", k=inputs["well_limits"].values["plume_limit"]),
             fmt("{x:,.0f} m", x=max(d.plume.values()) if d.plume else 0),
             t("downstream of the injection wells after {n} years", n=years)),
        ],
    }


def summary_table(d: design.Design, inputs: dict[str, SectionInput], name: str = "") -> pd.DataFrame:
    rows = [(t("Project"), t("Name"), name.strip() or "-", ""), (t("Project"), t("Date"), _today(), "")]
    for group, items in key_groups(d, inputs).items():
        rows += [(group, label, value, note) for label, value, note in items]
    rows += [(t("Design check"), c.title, c.detail, t(c.level)) for c in checks.result_checks(d, inputs)]
    return pd.DataFrame(rows, columns=[t("Group"), t("Item"), t("Value"), t("Note")])


def monthly_table(d: design.Design) -> pd.DataFrame:
    m = d.monthly.copy()
    m["month"] = list(i18n.months())
    return m.round(3).rename(columns={"month": t("Month"), "extraction_kwh": t("Extracted [kWh]"),
                                      "injection_kwh": t("Injected [kWh]"), "volume_m3": t("Water [m³]"),
                                      "spread_k": t("Mean change at injection [K]"), "pump_kwh": t("Pump [kWh]")})


def temperature_table(d: design.Design) -> pd.DataFrame:
    temps = d.temperatures.copy()
    return temps.round(3).rename(columns={"year": t("Year"), "month": t("Month"),
                                          "production": t("Production [°C]"), "injection": t("Injection [°C]"),
                                          "active": t("Running")})


def workbook(d: design.Design, inputs: dict[str, SectionInput], name: str = "") -> bytes:
    sheets = {t("Summary"): summary_table(d, inputs, name), t("Inputs"): inputs_table(inputs),
              t("Water and energy")[:31]: monthly_table(d), t("Temperatures"): temperature_table(d)}
    if d.tried:
        sheets[t("Distances tried")[:31]] = pd.DataFrame(d.tried).rename(columns={
            "distance": t("Distance [m]"), "production": t("Production wells"), "injection": t("Injection wells"),
            "result": t("Result")})
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for title, table in sheets.items():
            table.to_excel(writer, sheet_name=title, index=False)
            ws = writer.sheets[title]
            ws.freeze_panes = "A2"
            for col in ws.columns:
                width = max(len(str(c.value)) if c.value is not None else 0 for c in col[:200])
                ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
    return buf.getvalue()


def pdf(d: design.Design, inputs: dict[str, SectionInput], name: str = "") -> bytes:
    """Summary page with the key results and the design check, then the site map and the well construction."""
    from ..properties.ground import layered
    aquifer = design._build(inputs, "aquifer")
    buf = io.BytesIO()
    with PdfPages(buf) as pdf_file:
        fig = plt.figure(figsize=A4)
        y = 0.95
        fig.text(0.08, y, t("Groundwater wells: {name}", name=name.strip() or "-"), fontsize=15, weight="bold")
        y -= 0.025
        fig.text(0.08, y, _today(), fontsize=9, color="#666")
        y -= 0.04
        for group, rows in key_groups(d, inputs).items():
            fig.text(0.08, y, group, fontsize=11, weight="bold")
            y -= 0.022
            for label, value, note in rows:
                fig.text(0.1, y, label, fontsize=8.5)
                fig.text(0.55, y, value, fontsize=8.5, weight="bold")
                if note:
                    fig.text(0.1, y - 0.013, note, fontsize=7, color="#666")
                y -= 0.03
            y -= 0.01
        fig.text(0.08, y, t("Design check"), fontsize=11, weight="bold")
        y -= 0.022
        marks = {checks.PROBLEM: "✗", checks.WARNING: "!", checks.FINE: "✓"}
        for c in checks.result_checks(d, inputs):
            lines = textwrap.wrap(f"{marks[c.level]} {c.title}: {c.detail}", 110)
            for line in lines:
                if y < 0.04:
                    break
                fig.text(0.1, y, line, fontsize=7.5)
                y -= 0.016
        pdf_file.savefig(fig)
        plt.close(fig)
        for draw in (lambda: plots.site_map(d, aquifer),
                     lambda: plots.well_section(d, aquifer, list(inputs["ground"].values["layers"]["rows"])
                                                if layered(inputs["ground"].values) else None)):
            fig = draw()
            fig.set_size_inches(A4[0], A4[0] * 0.75)
            pdf_file.savefig(fig)
            plt.close(fig)
    return buf.getvalue()
