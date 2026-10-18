"""A PDF report of the inputs and results, made with matplotlib (no extra dependencies)."""
from __future__ import annotations

import datetime as dt
import io
import textwrap
from dataclasses import dataclass

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from . import analysis, i18n, model, plots, properties  # noqa: E402
from .i18n import fmt, t  # noqa: E402
from .properties import SectionInput  # noqa: E402

A4 = (8.27, 11.69)
METHOD = {"check": "Check of a given length", "hourly": "Sizing, hourly (L4)", "monthly": "Sizing, monthly (L2/L3)"}


def _today() -> str:
    """Today's date as written in the current language."""
    today = dt.date.today()
    return today.strftime("%d.%m.%Y") if i18n.language() == "de" else today.isoformat()


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
        rows = [(t("Type"), t(variant.label))]
        for p in variant.properties:
            v = chosen.values.get(p.key)
            if p.kind == "monthly":
                text = ", ".join(fmt("{m} {x:,.0f}", m=m, x=x) for m, x in zip(i18n.months(), v))
            elif p.kind == "points":
                text = t("{n} boreholes", n=len(v))
            elif p.kind == "layers":
                layer_rows = (v or {}).get("rows") or ()
                if not layer_rows:
                    continue
                text = (t("used: ") if v.get("use") else t("not used: ")) + "; ".join(
                    fmt("{top:g}–{bottom:g} m {rock} ({k:.2f})", top=r["top"], bottom=r["bottom"],
                        rock=t(r.get("rock", "")), k=float(r["k_s"])) for r in layer_rows)
            elif p.kind == "hourly":
                text = t("8760 h, heating {heat:,.0f} MWh (peak {heat_peak:,.0f} kW), cooling {cool:,.0f} MWh "
                         "(peak {cool_peak:,.0f} kW)", heat=sum(v["heating"]) / 1000, heat_peak=max(v["heating"]),
                         cool=sum(v["cooling"]) / 1000, cool_peak=max(v["cooling"]))
            elif isinstance(v, bool):
                text = t("yes") if v else t("no")
            elif isinstance(v, float):
                text = fmt("{x:,.0f}", x=v) if abs(v) >= 1000 else fmt("{x:.4g}", x=v)
            elif isinstance(v, str):
                text = t(v)
            else:
                text = fmt("{x}", x=v)
            rows.append((t(p.label), f"{text} {t(p.unit)}".strip()))
        blocks.append((t(section.label), rows))
    return blocks


def _temperature_figure(result: model.SizingResult, limits: dict) -> plt.Figure:
    t = result.temperatures
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=A4)
    for col, color in (("Average fluid (peak extraction)", plots.PIPE_UP),
                       ("Average fluid (peak injection)", plots.PIPE_DOWN),
                       ("Average fluid (base load)", "#555"), ("Borehole wall", "#aaa")):
        ax1.plot(t.index, t[col], label=i18n.t(col), color=color, lw=1.2)
    for ax in (ax1, ax2):
        ax.axhline(limits["T_min"], ls="--", color="gray", lw=0.8)
        ax.axhline(limits["T_max"], ls="--", color="gray", lw=0.8)
        ax.set_ylabel(i18n.t("Temperature [°C]"))
        ax.grid(alpha=0.3)
    ax1.set_xlabel(i18n.t("Time [years]"))
    ax1.set_title(i18n.t("Fluid temperatures over the simulation period"))
    ax1.legend(fontsize=7, loc="lower right")
    ext = analysis.yearly_extremes(result)
    ax2.plot(ext["Year"], ext["Lowest"], "o-", color=plots.PIPE_UP, label=i18n.t("Lowest"))
    ax2.plot(ext["Year"], ext["Highest"], "o-", color=plots.PIPE_DOWN, label=i18n.t("Highest"))
    ax2.set_xlabel(i18n.t("Year"))
    ax2.set_title(i18n.t("Lowest and highest average fluid temperature per year"))
    ax2.legend(fontsize=7)
    fig.tight_layout(pad=3)
    return fig


def _load_figure(result: model.SizingResult) -> plt.Figure:
    e = analysis.monthly_ground_energy(result)
    fig, ax = plt.subplots(figsize=(A4[0], A4[1] / 2.2))
    months = list(i18n.months())
    ax.bar(months, e["Extraction"], color=plots.PIPE_DOWN, label=t("Extraction"))
    ax.bar(months, -e["Injection"], color=plots.PIPE_UP, label=t("Injection"))
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel(t("Ground energy [MWh]"))
    ax.set_title(t("Monthly ground energy balance"))
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(pad=2)
    return fig


def _duration_figure(df) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(A4[0], A4[1] / 2.6))
    styles = {"Heating demand": (plots.HEATING, "-"), "Cooling demand": (plots.COOLING, "-"),
              "Ground extraction": (plots.HEATING, "--"), "Ground injection": (plots.COOLING, "--")}
    for col in df.columns[1:]:
        color, ls = styles.get(col, ("#555", "-"))
        ax.plot(df["Hours"], df[col], color=color, ls=ls, lw=1.2, label=t(col))
    ax.set_xlim(0, 8760)
    ax.set_xlabel(t("Hours per year"))
    ax.set_ylabel(t("Power [kW]"))
    ax.set_title(t("Load duration curve (first year)"))
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)
    fig.tight_layout(pad=2)
    return fig


def _hydraulics_figure(curve, flow: float, dp: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(A4[0], A4[1] / 2.6))
    ax.plot(curve["Flow per borehole [l/s]"], curve["Pressure drop [kPa]"], color=plots.PIPE_UP)
    ax.plot([flow], [dp], "ko")
    ax.annotate(t("design: {dp:.1f} kPa", dp=dp), (flow, dp), textcoords="offset points", xytext=(8, -12), fontsize=8)
    ax.set_xlabel(t("Flow rate per borehole [l/s]"))
    ax.set_ylabel(t("Pressure drop per borehole [kPa]"))
    ax.set_title(t("Pressure drop against flow rate (at the coldest fluid)"))
    ax.grid(alpha=0.3)
    fig.tight_layout(pad=2)
    return fig


def _ground_figure(m: dict) -> plt.Figure:
    table = m["table"]
    n = int(round(len(table) ** 0.5))
    X, Y, C = (table[c].to_numpy().reshape(n, n) for c in ("x", "y", "Change"))
    lim = max(m["max_change"], 0.1)
    fig, ax = plt.subplots(figsize=(A4[0], A4[0]))
    mesh = ax.pcolormesh(X, Y, C, cmap="RdBu_r", vmin=-lim, vmax=lim, shading="auto")
    ax.contour(X, Y, C, levels=8, colors="k", linewidths=0.4)
    ax.scatter(m["boreholes"]["x"], m["boreholes"]["y"], s=4, c="k")
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title(t("Ground temperature change at {depth:.0f} m depth after {years} years", depth=m["depth"],
                   years=m["years"]))
    fig.colorbar(mesh, ax=ax, label=t("Change [K]"), shrink=0.8)
    fig.tight_layout(pad=2)
    return fig


def _optimisation_figure(opt: dict) -> plt.Figure:
    mt = opt["monthly"]
    fig, ax = plt.subplots(figsize=(A4[0], A4[1] / 2.6))
    months = list(i18n.months())
    ax.bar(months, mt["Ground heating [MWh]"], color=plots.HEATING, label=t("Ground heating"))
    ax.bar(months, mt["External heating [MWh]"], bottom=mt["Ground heating [MWh]"], color="#f2c4ca",
           label=t("Backup heating"))
    ax.bar(months, -mt["Ground cooling [MWh]"], color=plots.COOLING, label=t("Ground cooling"))
    ax.bar(months, -mt["External cooling [MWh]"], bottom=-mt["Ground cooling [MWh]"], color="#bcdbe8",
           label=t("Backup cooling"))
    ax.axhline(0, color="black", lw=0.6)
    ax.set_ylabel(t("Building demand [MWh]"))
    ax.set_title(t("Load optimisation: heating {heat:.0%} and cooling {cool:.0%} covered by the ground",
                   heat=opt["heating_share"], cool=opt["cooling_share"]))
    ax.legend(fontsize=7, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout(pad=2)
    return fig


@dataclass
class ReportOptions:
    kind: str = "full"  # "full": cover, results, inputs, drawings and charts; "summary": one page
    title: str = ""
    subtitle: str = ""
    author: str = ""
    company: str = ""
    client: str = ""
    introduction: str = ""
    conclusion: str = ""
    logo: bytes | None = None  # PNG or JPEG


def _paragraphs(fig, text: str, y: float, width: int = 95, size: float = 9) -> float:
    for para in text.strip().split("\n"):
        for line in textwrap.wrap(para, width) or [""]:
            fig.text(0.08, y, line, fontsize=size)
            y -= 0.018
    return y


def _logo(fig, logo: bytes | None, box=(0.70, 0.88, 0.22, 0.09)) -> None:
    if not logo:
        return
    try:
        image = plt.imread(io.BytesIO(logo))
    except Exception:  # not an image matplotlib can read; the report goes out without it
        return
    ax = fig.add_axes(box)
    ax.imshow(image)
    ax.axis("off")


def _cover(pdf: PdfPages, opt: ReportOptions, title: str, summary: list[tuple[str, str]]) -> None:
    fig = plt.figure(figsize=A4)
    _logo(fig, opt.logo)
    fig.text(0.08, 0.80, title, fontsize=22, weight="bold")
    y = 0.765
    if opt.subtitle:
        fig.text(0.08, y, opt.subtitle, fontsize=13, color="#444")
        y -= 0.03
    y -= 0.02
    for label, value in ((t("Client"), opt.client),
                         (t("Prepared by"), ", ".join(x for x in (opt.author, opt.company) if x)),
                         (t("Date"), _today())):
        if value:
            fig.text(0.08, y, label, fontsize=10, color="#666")
            fig.text(0.30, y, value, fontsize=10)
            y -= 0.022
    y -= 0.03
    fig.text(0.08, y, t("Design"), fontsize=12, weight="bold")
    y -= 0.025
    for label, value in summary:
        fig.text(0.10, y, label, fontsize=10)
        fig.text(0.45, y, value, fontsize=10, weight="bold")
        y -= 0.021
    if opt.introduction:
        y -= 0.03
        fig.text(0.08, y, t("Introduction"), fontsize=12, weight="bold")
        _paragraphs(fig, opt.introduction, y - 0.025)
    pdf.savefig(fig)
    plt.close(fig)


def _summary_page(pdf: PdfPages, result, inputs, key, opt: ReportOptions, title: str,
                  summary: list[tuple[str, str]]) -> None:
    """Everything on one page: design, key results and the temperature chart."""
    fig = plt.figure(figsize=A4)
    _logo(fig, opt.logo, (0.74, 0.91, 0.18, 0.07))
    fig.text(0.06, 0.95, title, fontsize=17, weight="bold")
    sub = " · ".join(x for x in (opt.subtitle, opt.client, opt.company, opt.author, _today()) if x)
    fig.text(0.06, 0.928, sub, fontsize=8.5, color="#555")
    y = 0.895
    rows = summary + [(label, value) for items in key.by_group().values() for label, value, _ in items]
    half = (len(rows) + 1) // 2
    for col, part in ((0.06, rows[:half]), (0.53, rows[half:])):
        yy = y
        for label, value in part:
            fig.text(col, yy, label, fontsize=7)
            fig.text(col + 0.22, yy, textwrap.shorten(str(value), 38, placeholder="…"), fontsize=7,
                     weight="bold")
            yy -= 0.0165
    bottom = y - 0.0165 * half - 0.02
    ax = fig.add_axes((0.10, 0.08, 0.84, max(bottom - 0.10, 0.2)))
    t = result.temperatures
    limits = inputs["limits"].values
    if result.hourly_basis:
        h = result.hourly_temperatures["Average fluid"].to_numpy()
        days = h.reshape(-1, 24)
        x = (np.arange(len(days)) + 0.5) / 365
        ax.fill_between(x, days.min(axis=1), days.max(axis=1), color=plots.PIPE_UP, alpha=0.5, lw=0,
                        label=i18n.t("Average fluid, daily range (hourly)"))
    else:
        ax.plot(t.index, t["Average fluid (peak extraction)"], color=plots.PIPE_UP, lw=1, label=i18n.t("Peak heating"))
        ax.plot(t.index, t["Average fluid (peak injection)"], color=plots.PIPE_DOWN, lw=1,
                label=i18n.t("Peak cooling"))
    for lim in (limits["T_min"], limits["T_max"]):
        ax.axhline(lim, ls="--", color="gray", lw=0.8)
    ax.set_xlabel(i18n.t("Time [years]"))
    ax.set_ylabel(i18n.t("Average fluid temperature [°C]"))
    ax.legend(fontsize=7, loc="lower right")
    ax.grid(alpha=0.3)
    if key.warnings:
        fig.text(0.06, 0.03, i18n.t("Warnings: ") + " ".join(key.warnings)[:240], fontsize=7, color="#a33")
    pdf.savefig(fig)
    plt.close(fig)


def make_pdf(result: model.SizingResult, inputs: dict[str, SectionInput], project_name: str = "",
             options: ReportOptions | None = None, extras: dict | None = None) -> bytes:
    """The PDF report. extras may hold "ground_map" and "load_optimisation" results to include."""
    opt = options or ReportOptions()
    extras = extras or {}
    key = analysis.key_results(result, inputs)
    buf = io.BytesIO()
    with PdfPages(buf) as pdf:
        title = opt.title.strip() or project_name.strip() or t("Borefield design")
        summary = [(t("Calculation"), t(METHOD[result.sizing_method])),
                   (t("Simulation period"), t("{n} years", n=inputs["load"].values["simulation_period"])),
                   (t("Borehole length"), fmt("{x:.1f} m", x=result.borehole_length)),
                   (t("Number of boreholes"), str(result.number_of_boreholes)),
                   (t("Total borehole length"), fmt("{x:,.0f} m", x=result.total_length))]
        if opt.kind == "summary":
            _summary_page(pdf, result, inputs, key, opt, title, summary)
        else:
            _cover(pdf, opt, title, summary)
            blocks = [(group, [(label, value) for label, value, _ in rows])
                      for group, rows in key.by_group().items()]
            if key.warnings:
                blocks.append((t("Warnings"), [("!", w) for w in key.warnings]))
            _text_page(pdf, t("Results"), blocks)
            _text_page(pdf, t("Inputs"), _input_rows(inputs))

            drawings = plots.input_drawings(inputs)
            for _, drawing in drawings:
                for part in drawing if isinstance(drawing, tuple) else (drawing,):
                    if isinstance(part, plt.Figure):
                        pdf.savefig(part)
                        plt.close(part)
            figures = [_temperature_figure(result, inputs["limits"].values), _load_figure(result)]
            duration = analysis.load_duration(result)
            if duration is not None:
                figures.append(_duration_figure(duration))
            if "dp_kpa" in key.values:
                curve = analysis.pressure_drop_curve(result, key.values["t_min"])
                if curve is not None:
                    bf = result.borefield
                    flow = float(bf.borehole.flow_data.vfr_borehole(fluid_data=bf.borehole.fluid_data,
                                                                     temperature=key.values["t_min"]))
                    figures.append(_hydraulics_figure(curve, flow, key.values["dp_kpa"]))
            if extras.get("ground_map"):
                figures.append(_ground_figure(extras["ground_map"]))
            if extras.get("load_optimisation"):
                figures.append(_optimisation_figure(extras["load_optimisation"]))
            for fig in figures:
                pdf.savefig(fig)
                plt.close(fig)
            if opt.conclusion:
                fig = plt.figure(figsize=A4)
                fig.text(0.08, 0.95, t("Conclusion"), fontsize=16, weight="bold")
                _paragraphs(fig, opt.conclusion, 0.91)
                pdf.savefig(fig)
                plt.close(fig)
        pdf.infodict()["Title"] = title
        pdf.infodict()["Author"] = opt.author or opt.company
        pdf.infodict()["Creator"] = "GHEtool Web"
    return buf.getvalue()
