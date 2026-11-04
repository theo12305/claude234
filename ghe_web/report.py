"""The PDF report of the inputs and results (reportlab for the layout, the result charts as on the page).

Text flows over the pages (no fixed positions, so nothing overlaps), tables wrap long values, every page has a header
and a footer with the page number, and the charts are the ones of the results sheet, drawn at the page width. The
report follows the choice under "Customize the results" (``ReportOptions.sheet``): the same sections, charts and
temperature chart switches.
"""
from __future__ import annotations

import datetime as dt
import functools
import io
import pathlib
from dataclasses import dataclass, replace
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_RIGHT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepInFrame, KeepTogether,  # noqa: E402
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)

from . import analysis, i18n, model, plots, properties  # noqa: E402
from .i18n import fmt, t  # noqa: E402
from .properties import SectionInput  # noqa: E402

METHOD = {"check": "Check of a given length", "hourly": "Sizing, hourly (L4)", "monthly": "Sizing, monthly (L2/L3)"}
APP_NAME = "GHEtool & Co."

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
TEXT_W = PAGE_W - 2 * MARGIN
NAVY, ACCENT, MUTED, LINE = (colors.HexColor(c) for c in ("#13294b", "#0e7490", "#64748b", "#d5dde8"))
SOFT = colors.HexColor("#f1f5f9")


def _today() -> str:
    """Today's date as written in the current language."""
    today = dt.date.today()
    return today.strftime("%d.%m.%Y") if i18n.language() == "de" else today.isoformat()


# ---------------------------------------------------------------- fonts and text styles

FONT_DIR = pathlib.Path(matplotlib.get_data_path()) / "fonts" / "ttf"  # DejaVu ships with matplotlib


@functools.cache
def _fonts() -> tuple[str, str]:
    """DejaVu Sans (all the symbols used: ², ³, ≈, ×, Δ, ...), or Helvetica if it cannot be loaded."""
    try:
        pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu",
                                      boldItalic="DejaVu-Bold")
        return "DejaVu", "DejaVu-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


@functools.cache
def _styles() -> dict[str, ParagraphStyle]:
    font, bold = _fonts()
    base = ParagraphStyle("base", fontName=font, fontSize=9, leading=12.5, textColor=colors.HexColor("#1e293b"))
    return {
        "body": base,
        "small": ParagraphStyle("small", base, fontSize=7.8, leading=10, textColor=MUTED),
        "cell": ParagraphStyle("cell", base, fontSize=8.4, leading=11),
        "cellb": ParagraphStyle("cellb", base, fontName=bold, fontSize=8.4, leading=11),
        "cellr": ParagraphStyle("cellr", base, fontName=bold, fontSize=8.4, leading=11, alignment=TA_RIGHT),
        "title": ParagraphStyle("title", base, fontName=bold, fontSize=24, leading=29, textColor=NAVY),
        "subtitle": ParagraphStyle("subtitle", base, fontSize=13, leading=17, textColor=MUTED),
        "h1": ParagraphStyle("h1", base, fontName=bold, fontSize=15, leading=19, textColor=NAVY, spaceBefore=4,
                             spaceAfter=8),
        "h2": ParagraphStyle("h2", base, fontName=bold, fontSize=11, leading=14, textColor=NAVY, spaceBefore=10,
                             spaceAfter=5),
        "fig": ParagraphStyle("fig", base, fontName=bold, fontSize=9.5, leading=12.5, spaceBefore=8, spaceAfter=3),
        "big": ParagraphStyle("big", base, fontName=bold, fontSize=20, leading=25, textColor=NAVY),
        "warn": ParagraphStyle("warn", base, fontSize=8.4, leading=11, textColor=colors.HexColor("#92400e")),
    }


def _p(text: str, style: str = "body") -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), _styles()[style])


# ---------------------------------------------------------------- pictures

@functools.cache
def _register_chart_fonts() -> None:
    import vl_convert as vlc
    try:
        vlc.register_font_directory(str(FONT_DIR))
    except Exception:
        pass


def chart_png(chart, width: int = 700, height: int | None = None, scale: float = 2.0) -> bytes:
    """An Altair chart as PNG, with a white background, the number format of the language and fonts that are
    always there (DejaVu from matplotlib), without its title (the report writes it above)."""
    import vl_convert as vlc
    _register_chart_fonts()
    spec = i18n.localize_chart(chart).to_dict(validate=False)
    spec.pop("title", None)
    config = {**spec.get("config", {}), **i18n.chart_config(background="white").to_dict(validate=False)}
    config["font"] = "DejaVu Sans"
    spec["config"] = config
    if "width" not in spec:
        spec["width"] = width
    if height is not None:
        spec["height"] = height
    return vlc.vegalite_to_png(spec, scale=scale)


def _image(png: bytes, max_w: float = TEXT_W, max_h: float = 120 * mm) -> Image:
    """A picture scaled to fit the width and a height, keeping its proportions."""
    from reportlab.lib.utils import ImageReader
    w, h = ImageReader(io.BytesIO(png)).getSize()
    k = min(max_w / w, max_h / h)
    img = Image(io.BytesIO(png), width=w * k, height=h * k)
    img.hAlign = "CENTER"
    return img


def _figure_png(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


# ---------------------------------------------------------------- tables

def _table(rows: list[tuple], widths: list[float], header: list[str] | None = None, zebra: bool = True) -> Table:
    """Rows of texts as a table that wraps long values; the last column is right-aligned and bold."""
    data = []
    if header:
        data.append([_p(h, "cellb") for h in header])
    for row in rows:
        cells = [_p(c, "cell") for c in row[:-1]] + [_p(row[-1], "cellr")]
        data.append(cells)
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3), ("LEFTPADDING", (0, 0), (-1, -1), 5),
             ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE)]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), SOFT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, NAVY)]
    if zebra:
        start = 1 if header else 0
        style += [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8fafc"))
                  for i in range(start + 1, len(data), 2)]
    table.setStyle(TableStyle(style))
    return table


def _key_table(rows: list[tuple[str, str, str]], width: float) -> Table:
    data = []
    for label, value, note in rows:
        cell = [_p(label, "cell")] + ([_p(note, "small")] if note else [])
        data.append([cell, _p(value, "cellr")])
    table = Table(data, colWidths=[width * 0.56, width * 0.44], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
                               ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                               ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return table


def _input_rows(inputs: dict[str, SectionInput]) -> list[tuple[str, list[tuple[str, str]]]]:
    blocks = []
    for section in properties.sections():
        chosen = inputs.get(section.key)
        if chosen is None or (section.system and inputs.get("system") is not None
                              and section.system != inputs["system"].variant):
            continue
        variant = section.variant(chosen.variant)
        rows = [(t("Type"), t(variant.label))] if len(section.variants) > 1 else []
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
        if rows:
            blocks.append((t(section.label), rows))
    return blocks


# ---------------------------------------------------------------- options

@dataclass
class ReportOptions:
    kind: str = "full"  # "full": cover, results, charts, inputs and drawings; "summary": one page
    title: str = ""
    subtitle: str = ""
    author: str = ""
    company: str = ""
    client: str = ""
    introduction: str = ""
    conclusion: str = ""
    logo: bytes | None = None  # PNG or JPEG
    sheet: dict | None = None  # results/sheet.choice(): sections, parts and chart switches; None = the standard sheet
    inputs: bool = True  # the input tables and drawings (full report)


def _sheet(opt: ReportOptions) -> tuple[dict, dict, plots.ChartStyle]:
    from .results.sheet import PARTS, SECTION_DEFAULTS
    choice = opt.sheet or {}
    sections = {**SECTION_DEFAULTS, **choice.get("sections", {})}
    parts = {p: d for group in PARTS.values() for p, _, d in group} | choice.get("parts", {})
    style = choice.get("style") or plots.DEFAULT_STYLE
    return sections, parts, replace(style, pointer=False)  # nothing to point at on paper


# ---------------------------------------------------------------- the document

class _Doc(BaseDocTemplate):
    def __init__(self, buf, title: str, opt: ReportOptions):
        super().__init__(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN + 8 * mm,
                         bottomMargin=MARGIN + 4 * mm, title=title, author=opt.author or opt.company,
                         creator=APP_NAME, subject=t("Borefield design"))
        self.report_title, self.opt = title, opt
        frame = Frame(MARGIN, MARGIN + 4 * mm, TEXT_W, PAGE_H - 2 * MARGIN - 12 * mm, id="body",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate("first", [frame], onPage=self._first),
                               PageTemplate("page", [frame], onPage=self._page)])
        self._logo = None
        if opt.logo:
            try:
                from reportlab.lib.utils import ImageReader
                self._logo = ImageReader(io.BytesIO(opt.logo))
            except Exception:  # not an image reportlab can read; the report goes out without it
                self._logo = None

    def _footer(self, canvas) -> None:
        font, _ = _fonts()
        canvas.setFont(font, 7.5)
        canvas.setFillColor(MUTED)
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, MARGIN, PAGE_W - MARGIN, MARGIN)
        left = " · ".join(x for x in (APP_NAME, self.opt.company, _today()) if x)
        canvas.drawString(MARGIN, MARGIN - 4 * mm, left)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 4 * mm, t("Page {n}", n=canvas.getPageNumber()))

    def _draw_logo(self, canvas, x_right: float, y_top: float, h: float) -> None:
        if self._logo is None:
            return
        w0, h0 = self._logo.getSize()
        w = min(h * w0 / h0, 45 * mm)
        hh = w * h0 / w0
        canvas.drawImage(self._logo, x_right - w, y_top - hh, w, hh, mask="auto")

    def _first(self, canvas, doc) -> None:
        canvas.saveState()
        self._draw_logo(canvas, PAGE_W - MARGIN, PAGE_H - 6 * mm, 14 * mm)
        self._footer(canvas)
        canvas.restoreState()

    def _page(self, canvas, doc) -> None:
        canvas.saveState()
        font, bold = _fonts()
        y = PAGE_H - MARGIN + 1 * mm
        canvas.setFont(bold, 9)
        canvas.setFillColor(NAVY)
        canvas.drawString(MARGIN, y, self.report_title[:90])
        self._draw_logo(canvas, PAGE_W - MARGIN, y + 6 * mm, 8 * mm)
        canvas.setStrokeColor(LINE)
        canvas.line(MARGIN, y - 3 * mm, PAGE_W - MARGIN, y - 3 * mm)
        self._footer(canvas)
        canvas.restoreState()


def _answer_box(result, key, inputs) -> Table:
    """The design in a box: n × length, total, method and the fluid range."""
    vals = key.values
    years = inputs["load"].values["simulation_period"]
    big = t("{n} boreholes × {length:.1f} m", n=result.number_of_boreholes, length=result.borehole_length)
    sub = t("{total:,.0f} m drilled · fluid between {lo:.1f} and {hi:.1f} °C over {years} years",
            total=result.total_length, lo=round(vals["t_min"], 1) + 0.0, hi=round(vals["t_max"], 1) + 0.0,
            years=years)
    if result.sizing_method == "check":
        verdict = t("The given length keeps the fluid within the limits.") if vals.get("passes") else \
            t("The given length does not keep the fluid within the limits.")
        sub += " · " + verdict
    lead = t("Check of the given length") if result.sizing_method == "check" else t("Answer")
    cell = [_p(lead, "small"), _p(big, "big"), Spacer(1, 2), _p(sub, "body"),
            _p(t(METHOD[result.sizing_method]), "small")]
    box = Table([[cell]], colWidths=[TEXT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ecfeff")),
                             ("BOX", (0, 0), (-1, -1), 0.8, ACCENT), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                             ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 8),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    return box


def _warnings(key) -> list:
    if not key.warnings:
        return []
    rows = [[_p("⚠ " + w, "warn")] for w in key.warnings]
    box = Table(rows, colWidths=[TEXT_W])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 3),
                             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return [Spacer(1, 6), box]


def _key_groups(key, width: float = TEXT_W) -> list:
    """The key results group by group, in two columns."""
    groups = list(key.by_group().items())
    half = (TEXT_W - 8 * mm) / 2
    columns, heights = ([], []), [0, 0]
    for group, rows in groups:
        side = heights.index(min(heights))
        columns[side].extend([_p(group, "h2"), _key_table(rows, half)])
        heights[side] += len(rows) + 2
    grid = Table([[columns[0], columns[1]]], colWidths=[half + 4 * mm, half + 4 * mm])
    grid.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 8 * mm / 2)]))
    return [grid]


class _Figures:
    """Numbered figures: title above, the picture, the caption below, kept together on one page."""

    def __init__(self):
        self.n = 0

    def add(self, title: str, png: bytes, caption: str = "", max_h: float = 105 * mm,
            keep: bool = True) -> KeepTogether | list:
        self.n += 1
        parts = [_p(t("Figure {n}", n=self.n) + " · " + title, "fig"), _image(png, max_h=max_h)]
        if caption:
            parts.append(_p(caption, "small"))
        parts.append(Spacer(1, 8))
        return KeepTogether(parts) if keep else parts


def _result_figures(result, inputs, key, opt: ReportOptions, extras: dict, figs: _Figures) -> list:
    """The charts of the results sheet that are switched on, section by section."""
    sections, parts, style = _sheet(opt)
    limits = inputs["limits"].values
    story: list = []

    def heading(text: str) -> None:  # never alone at the bottom of a page: room for it and a chart
        story.extend([CondPageBreak(115 * mm), _p(text, "h1")])

    if sections.get("temperatures"):
        heading(t("Temperatures"))
        temps = result.temperatures
        if parts.get("temp_years"):
            story.append(figs.add(t("Fluid temperature in the boreholes over {n} years",
                                    n=round(float(temps.index.max()))),
                                  chart_png(plots.temperature_chart(temps, limits, None, style), 700, 320),
                                  t("Blue: the fluid at the heating peaks, the coldest. Red: at the cooling peaks, the "
                                    "warmest. Grey: without peaks. Dashed: the temperature limits.")))
        if parts.get("temp_zoom") or parts.get("temp_last"):
            story.append(figs.add(t("Last year of the simulation"),
                                  chart_png(plots.last_year_chart(temps, limits, style=style), 700, 240)))
        if parts.get("temp_extremes"):
            extremes = analysis.yearly_extremes(result)
            story.append(figs.add(t("Lowest and highest temperature per year"),
                                  chart_png(plots.yearly_extremes_chart(extremes, limits, style), 700, 224)))
    if sections.get("energy"):
        heading(t("Energy"))
        if parts.get("energy_balance"):
            energy = analysis.monthly_ground_energy(result)
            story.append(figs.add(t("Monthly energy balance of the ground"),
                                  chart_png(plots.energy_balance_chart(energy), 700, 264)))
        if parts.get("energy_numbers"):
            story.append(_table([(t("Extracted from the ground"), t("{x:,.0f} MWh/yr", x=key.values["extraction_mwh"])),
                                 (t("Injected into the ground"), t("{x:,.0f} MWh/yr", x=key.values["injection_mwh"])),
                                 (t("Imbalance"), t("{x:+,.0f} MWh/yr", x=key.values["imbalance_mwh"]))],
                                [TEXT_W * 0.6, TEXT_W * 0.4]))
            story.append(Spacer(1, 8))
        duration = analysis.load_duration(result) if parts.get("load_duration") else None
        if duration is not None:
            story.append(figs.add(t("Load duration curve (first year)"),
                                  chart_png(plots.load_duration_chart(duration), 700, 224)))
    hourly = result.hourly_temperatures
    if sections.get("hourly") and hourly is not None:
        heading(t("Hourly"))
        if parts.get("hourly_daily"):
            story.append(figs.add(t("Hourly fluid temperature (daily range)"),
                                  chart_png(plots.hourly_band_chart(hourly, limits, style), 700, 240)))
        if parts.get("hourly_last"):
            story.append(figs.add(t("Hourly fluid temperature in the last year"),
                                  chart_png(plots.hourly_last_year_chart(hourly, limits, style), 700, 240)))
        if parts.get("hourly_heatmap"):
            story.append(figs.add(t("Heat map of the last year"), chart_png(plots.heatmap_chart(hourly), 700, 240)))
    if sections.get("ground") and (extras.get("ground_map") or parts.get("gfunction")):
        heading(t("Ground"))
        m = extras.get("ground_map")
        if m and parts.get("ground_map"):
            north = inputs["borefield"].variant == "custom"
            story.append(figs.add(t("Ground temperature change at {depth:.0f} m depth after {years} years",
                                    depth=m["depth"], years=m["years"]),
                                  chart_png(plots.ground_map_chart(m, north, size=520), scale=2), max_h=125 * mm))
        if parts.get("gfunction"):
            curve = analysis.gfunction_curve(result)
            story.append(figs.add(t("g-function of the borefield (thermal interaction of the boreholes)"),
                                  chart_png(plots.gfunction_chart(curve), 700, 224)))
    if sections.get("field") and extras.get("borehole_map") is not None and len(extras["borehole_map"]) > 1:
        heading(t("Borefield map"))
        story.append(figs.add(t("Share of the load"),
                              chart_png(plots.borehole_map_chart(extras["borehole_map"], "share"), scale=2),
                              max_h=120 * mm))
    if sections.get("load_optimisation") and extras.get("load_optimisation"):
        opt_ = extras["load_optimisation"]
        heading(t("Load optimisation"))
        story.append(figs.add(t("Load optimisation: heating {heat:.0%} and cooling {cool:.0%} covered by the ground",
                                heat=opt_["heating_share"], cool=opt_["cooling_share"]),
                              chart_png(plots.optimisation_chart(opt_["monthly"]), 700, 240)))
    return story


def _drawings(inputs, figs: _Figures) -> list:
    story = []
    for title, drawing in plots.input_drawings(inputs):
        for part in drawing if isinstance(drawing, tuple) else (drawing,):
            png = _figure_png(part) if isinstance(part, plt.Figure) else chart_png(part, 700, 224)
            story.append(figs.add(title, png, max_h=95 * mm))
    return story


def make_pdf(result: model.SizingResult, inputs: dict[str, SectionInput], project_name: str = "",
             options: ReportOptions | None = None, extras: dict | None = None) -> bytes:
    """The PDF report. extras may hold "ground_map", "borehole_map" and "load_optimisation" results to include."""
    opt = options or ReportOptions()
    extras = extras or {}
    key = analysis.key_results(result, inputs)
    title = opt.title.strip() or project_name.strip() or t("Borefield design")
    buf = io.BytesIO()
    doc = _Doc(buf, title, opt)
    figs = _Figures()
    sections, parts, style = _sheet(opt)

    head = [_p(title, "title")]
    if opt.subtitle:
        head.append(_p(opt.subtitle, "subtitle"))
    meta = [(t("Client"), opt.client), (t("Prepared by"), ", ".join(x for x in (opt.author, opt.company) if x)),
            (t("Date"), _today())]
    meta_rows = [(label, value) for label, value in meta if value]
    meta_table = Table([[_p(a, "small"), _p(b, "cell")] for a, b in meta_rows], colWidths=[32 * mm, TEXT_W - 32 * mm],
                       hAlign="LEFT")
    meta_table.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 1),
                                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))

    if opt.kind == "summary":
        story = [*head, Spacer(1, 4), meta_table, Spacer(1, 8), _answer_box(result, key, inputs), Spacer(1, 4)]
        story += _key_groups(key)
        if result.hourly_basis:
            png = chart_png(plots.hourly_band_chart(result.hourly_temperatures, inputs["limits"].values, style),
                            900, 300)
        else:
            png = chart_png(plots.temperature_chart(result.temperatures, inputs["limits"].values, None, style),
                            900, 320)
        story += [Spacer(1, 6), *figs.add(t("Fluid temperature over the years"), png, max_h=80 * mm, keep=False)]
        story += _warnings(key)
        frame_h = PAGE_H - 2 * MARGIN - 12 * mm
        doc.build([KeepInFrame(TEXT_W, frame_h, story, mode="shrink")])
        return buf.getvalue()

    story = [NextPageTemplate("page"), Spacer(1, 30 * mm), *head, Spacer(1, 8), meta_table, Spacer(1, 14),
             _answer_box(result, key, inputs)]
    if opt.introduction:
        story += [Spacer(1, 10), _p(t("Introduction"), "h2"), _p(opt.introduction)]
    story += _warnings(key)
    story += [PageBreak(), _p(t("Results"), "h1")]
    story += _key_groups(key)
    story += _result_figures(result, inputs, key, opt, extras, figs)
    if opt.conclusion:
        story += [CondPageBreak(40 * mm), _p(t("Conclusion"), "h1"), _p(opt.conclusion)]
    if opt.inputs:
        story += [PageBreak(), _p(t("Inputs"), "h1")]
        for heading, rows in _input_rows(inputs):
            story.append(KeepTogether([_p(heading, "h2"),
                                       _table(rows, [TEXT_W * 0.45, TEXT_W * 0.55], zebra=True)]))
        drawings = _drawings(inputs, figs)
        if drawings:
            story += [CondPageBreak(80 * mm), _p(t("Drawings of the inputs"), "h1"), *drawings]
    doc.build(story)
    return buf.getvalue()
