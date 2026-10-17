"""A PDF report of the inputs and results, made with matplotlib (no extra dependencies)."""
from __future__ import annotations

import datetime as dt
import io
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from . import analysis, model, plots, properties  # noqa: E402
from .properties import SectionInput  # noqa: E402
from .properties.load import MONTHS  # noqa: E402

A4 = (8.27, 11.69)


def _text_page(pdf: PdfPages, title: str, blocks: list[tuple[str, list[tuple[str, str]]]]) -> None:
    """Write headed tables of (label, value) on as many pages as needed."""
    fig = plt.figure(figsize=A4)
    y = 0.95
    fig.text(0.08, y, title, fontsize=16, weight="bold")
    y -= 0.04
    for heading, rows in blocks:
        if y < 0.12:
            pdf.savefig(fig)
            plt.close(fig)
            fig, y = plt.figure(figsize=A4), 0.95
        fig.text(0.08, y, heading, fontsize=11, weight="bold")
        y -= 0.022
        for label, value in rows:
            lines = textwrap.wrap(str(value), 55) or [""]
            fig.text(0.10, y, label, fontsize=8.5)
            for line in lines:
                fig.text(0.52, y, line, fontsize=8.5)
                y -= 0.016
            if y < 0.06:
                pdf.savefig(fig)
                plt.close(fig)
                fig, y = plt.figure(figsize=A4), 0.95
        y -= 0.012
    pdf.savefig(fig)
    plt.close(fig)


def _input_rows(inputs: dict[str, SectionInput]) -> list[tuple[str, list[tuple[str, str]]]]:
    blocks = []
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None:
            continue
        variant = section.variant(chosen.variant)
        rows = [("Type", variant.label)]
        for p in variant.properties:
            v = chosen.values.get(p.key)
            if p.kind == "monthly":
                text = ", ".join(f"{m} {x:,.0f}" for m, x in zip(MONTHS, v))
            elif p.kind == "points":
                text = f"{len(v)} boreholes"
            elif p.kind == "hourly":
                text = (f"8760 h, heating {sum(v['heating']) / 1000:,.0f} MWh (peak {max(v['heating']):,.0f} kW), "
                        f"cooling {sum(v['cooling']) / 1000:,.0f} MWh (peak {max(v['cooling']):,.0f} kW)")
            elif isinstance(v, float):
                text = f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.4g}"
            else:
                text = str(v)
            rows.append((p.label, f"{text} {p.unit}".strip()))
        blocks.append((section.label, rows))
    return blocks


def _temperature_figure(result: model.SizingResult, limits: dict) -> plt.Figure:
    t = result.temperatures
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=A4)
    for col, color in (("Average fluid (peak extraction)", plots.PIPE_UP),
                       ("Average fluid (peak injection)", plots.PIPE_DOWN),
                       ("Average fluid (base load)", "#555"), ("Borehole wall", "#aaa")):
        ax1.plot(t.index, t[col], label=col, color=color, lw=1.2)
    for ax in (ax1, ax2):
        ax.axhline(limits["T_min"], ls="--", color="gray", lw=0.8)
        ax.axhline(limits["T_max"], ls="--", color="gray", lw=0.8)
        ax.set_ylabel("Temperature [°C]")
        ax.grid(alpha=0.3)
    ax1.set_xlabel("Time [years]")
    ax1.set_title("Fluid temperatures over the simulation period")
    ax1.legend(fontsize=7, loc="lower right")
    ext = analysis.yearly_extremes(result)
    ax2.plot(ext["Year"], ext["Lowest"], "o-", color=plots.PIPE_UP, label="Lowest")
    ax2.plot(ext["Year"], ext["Highest"], "o-", color=plots.PIPE_DOWN, label="Highest")
    ax2.set_xlabel("Year")
    ax2.set_title("Lowest and highest average fluid temperature per year")
    ax2.legend(fontsize=7)
    fig.tight_layout(pad=3)
    return fig


def _load_figure(result: model.SizingResult) -> plt.Figure:
    e = analysis.monthly_ground_energy(result)
    fig, ax = plt.subplots(figsize=(A4[0], A4[1] / 2.2))
    ax.bar(e["Month"], e["Extraction"], color=plots.PIPE_DOWN, label="Extraction")
    ax.bar(e["Month"], -e["Injection"], color=plots.PIPE_UP, label="Injection")
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel("Ground energy [MWh]")
    ax.set_title("Monthly ground energy balance")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(pad=2)
    return fig


def make_pdf(result: model.SizingResult, inputs: dict[str, SectionInput], project_name: str = "") -> bytes:
    key = analysis.key_results(result, inputs)
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        title = project_name.strip() or "Borefield design"
        summary = [("Date", dt.date.today().isoformat()),
                   ("Calculation", {"check": "check of a given length", "hourly": "sizing, hourly (L4)",
                                    "monthly": "sizing, monthly (L2/L3)"}[result.sizing_method]),
                   ("Borehole length", f"{result.borehole_length:.1f} m"),
                   ("Number of boreholes", str(result.number_of_boreholes)),
                   ("Total length", f"{result.total_length:,.0f} m")]
        blocks = [("Summary", summary), ("Key results", [(label, value) for label, value, _ in key.rows])]
        if key.warnings:
            blocks.append(("Warnings", [("!", w) for w in key.warnings]))
        _text_page(pdf, title, blocks)
        _text_page(pdf, "Inputs", _input_rows(inputs))

        drawings = plots.input_drawings(inputs)
        for _, drawing in drawings:
            for part in drawing if isinstance(drawing, tuple) else (drawing,):
                if isinstance(part, plt.Figure):
                    pdf.savefig(part)
                    plt.close(part)
        for fig in (_temperature_figure(result, inputs["limits"].values), _load_figure(result)):
            pdf.savefig(fig)
            plt.close(fig)
        pdf.infodict()["Title"] = title
        pdf.infodict()["Creator"] = "GHEtool Web"
    return buf.getvalue()
