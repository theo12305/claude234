"""The look of the page (Streamlit): colours for light and dark mode, the app bar, the answer card and key tiles of
the results, the range bars next to the inputs and the calculate bar fixed at the bottom of the screen."""
from __future__ import annotations

import html
import io
import re
import textwrap

import streamlit as st

from ghe_web import i18n
from ghe_web.charts import palette
from ghe_web.i18n import t
from ghe_web.page import guidance

# Light and dark colours. The Streamlit theme (.streamlit/config.toml) uses the same values.
PALETTE = {
    "light": {"bg": "#f6f8fb", "card": "#ffffff", "line": "#e2e8f0", "text": "#1e293b", "muted": "#64748b",
              "bar": "#13294b", "bar_text": "#e2e8f0", "accent": "#0e7490", "band": "#a7f3d0", "track": "#e2e8f0",
              "answer": "linear-gradient(90deg,#ecfeff 0%,#ffffff 70%)", "shadow": "0 1px 3px rgba(15,23,42,.08),"
              "0 4px 14px rgba(15,23,42,.05)", "cold": "#1d4ed8", "warm": "#c2410c"},
    "dark": {"bg": "#0f172a", "card": "#162133", "line": "#2b3a52", "text": "#e2e8f0", "muted": "#94a3b8",
             "bar": "#16294a", "bar_text": "#e2e8f0", "accent": "#22a3c4", "band": "#166534", "track": "#334155",
             "answer": "linear-gradient(90deg,#123040 0%,#162133 70%)", "shadow": "0 1px 3px rgba(0,0,0,.4)",
             "cold": "#60a5fa", "warm": "#fb923c"},
}

# The logo: a gradient tile (warm above, cool below) with three boreholes, drawn with CSS (no image file).
LOGO = "<div class='logo'><i></i><i></i><i></i></div>"


def favicon():
    """The logo as the browser tab icon: the gradient tile with three boreholes (as LOGO), drawn at 96 px."""
    from PIL import Image, ImageDraw
    size = 96
    top, bottom = (0xF9, 0x73, 0x16), (0x0E, 0x74, 0x90)
    tile = Image.new("RGBA", (size, size))
    for y in range(size):
        k = y / (size - 1)
        tile.paste(tuple(round(a + (b - a) * k) for a, b in zip(top, bottom)) + (255,), (0, y, size, y + 1))
    draw = ImageDraw.Draw(tile)
    for x, h in ((33, 50), (46, 60), (59, 50)):
        draw.rounded_rectangle((x, 23, x + 7, 23 + h), radius=3, fill="white")
    mask = Image.new("L", (size, size))
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=24, fill=255)
    tile.putalpha(mask)
    return tile


def is_phone() -> bool:
    """True on a phone (by the browser's user agent; tablets count as wide screens). Charts then get legends in
    one column and wrapped titles, and fixed-size charts a smaller size."""
    try:
        agent = st.context.headers.get("User-Agent", "") or ""
    except Exception:
        return False
    return ("Mobi" in agent or "iPhone" in agent) and "iPad" not in agent


def _for_phone(spec: dict) -> dict:
    """Adapts a Vega-Lite spec to a narrow screen: legends above the chart in one column instead of one long row,
    and titles wrapped instead of cut off with "…"."""
    def walk(node):
        if isinstance(node, dict):
            legend = node.get("legend")
            if isinstance(legend, dict) and legend.get("orient", "top") == "top":
                legend.update(columns=1, labelLimit=330)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(spec)
    title = spec.get("title")
    if isinstance(title, str):
        spec["title"] = textwrap.wrap(title, 40) or title
    elif isinstance(title, dict) and isinstance(title.get("text"), str):
        title["text"] = textwrap.wrap(title["text"], 40) or title["text"]
    return spec


def show_chart(c, width="stretch", title: bool = True) -> None:
    """An Altair chart in the current language's number format. ``title=False`` leaves the chart's own title out
    (the page shows it above the chart, where it can wrap)."""
    # no schema validation on every page run: the charts are fixed code and covered by the tests (saves ~0.1 s/chart)
    spec = i18n.localize_chart(c).to_dict(validate=False)
    # no own background: the chart sits on the card or page it is drawn on (the theme gives the page grey)
    spec["config"] = {**spec.get("config", {}), "background": "transparent"}
    spec = palette.with_theme(spec, dark=theme() == "dark")  # one chart look (ghe_web/charts/palette.py)
    if not title:
        spec.pop("title", None)
    if is_phone():
        spec = _for_phone(spec)
    st.vega_lite_chart(spec, width=width)


def figure_svg(fig) -> str:
    """A Matplotlib figure as SVG: sharp at every zoom and on every screen. The text is drawn as outlines, so it
    looks the same everywhere. The figure is closed."""
    import matplotlib.pyplot as plt
    buf = io.StringIO()
    with plt.rc_context({"svg.fonttype": "path", "svg.hashsalt": "ghe"}):
        fig.savefig(buf, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    svg = buf.getvalue()
    return re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)  # no creation date: same drawing, same text


def show_figure(fig_or_svg) -> None:
    """A drawing (Matplotlib figure or SVG text from ``figure_svg``) on a white sheet, sharp on every screen. It
    fills the column up to 1.6 × its own size."""
    import base64
    svg = fig_or_svg if isinstance(fig_or_svg, str) else figure_svg(fig_or_svg)
    width = re.search(r'<svg[^>]*?width="([\d.]+)pt"', svg)
    natural = float(width.group(1)) * 1.6 if width else 600
    data = base64.b64encode(svg.encode()).decode()
    st.html(f"<div class='drawing'><img src='data:image/svg+xml;base64,{data}' alt='' "
            f"style='width:100%;max-width:{natural:.0f}px;height:auto'></div>")


def theme() -> str:
    try:
        kind = st.context.theme.type
    except Exception:
        kind = None
    return kind if kind in PALETTE else "light"


def inject_css() -> None:
    c = PALETTE[theme()]
    # dark mode: the drawings in dark colours (inverted, hues kept) instead of a white sheet
    dark_drawing = (".drawing {background: #0b1220; border-color: var(--line); box-shadow: none;}\n"
                    ".drawing img {filter: invert(1) hue-rotate(180deg) brightness(.92) contrast(.95);}"
                    if theme() == "dark" else "")
    st.html(f"""<style>
:root {{--card:{c['card']};--line:{c['line']};--muted:{c['muted']};--accent:{c['accent']};--bar:{c['bar']};
  --bar-text:{c['bar_text']};--band:{c['band']};--track:{c['track']};--shadow:{c['shadow']};--cold:{c['cold']};
  --warm:{c['warm']};--answer:{c['answer']};}}
/* the page grows with the screen: full width up to very wide monitors, side margins scale with the width */
.block-container {{padding-top: 3.2rem; padding-bottom: 8rem; max-width: 2400px;
  padding-left: clamp(1rem, 2.5vw, 3.5rem); padding-right: clamp(1rem, 2.5vw, 3.5rem);}}
/* key figures (st.metric) look like the tiles of the results */
[data-testid="stMetric"] {{background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  padding: 12px 16px; box-shadow: var(--shadow); height: 100%;}}
[data-testid="stMetricLabel"] p {{font-size: .85rem; color: var(--muted);}}
[data-testid="stMetricValue"] {{font-size: 1.45rem; font-weight: 700;}}
h1, h2, h3, h4, h5 {{letter-spacing: -0.01em;}}
/* cards: containers get the card colour (the bordered ones are the input sections and result boxes) */
div[data-testid="stVerticalBlock"][data-test-scroll-behavior] {{background: var(--card);}}
.st-key-welcome, .st-key-quick_downloads, .st-key-calcbar div[data-testid="stVerticalBlock"],
.st-key-appbar div[data-testid="stVerticalBlock"] {{background: transparent !important;}}
/* tabs: the input steps, each with its icon; the open one on a light tint of the accent */
.st-key-step [role="tablist"] {{gap: 4px;}}
.st-key-step [role="tab"] {{padding: 6px 12px; border-radius: 10px 10px 0 0;}}
.st-key-step [role="tab"] [data-testid="stIconMaterial"] {{color: var(--muted); font-size: 1.15rem;}}
.st-key-step [role="tab"][aria-selected="true"] {{background: color-mix(in srgb, var(--accent) 9%, transparent);}}
.st-key-step [role="tab"][aria-selected="true"] [data-testid="stIconMaterial"] {{color: var(--accent);}}
/* section headings: the name with an icon on a light tint (ground warm, water and borehole cool, loads red,
   limits and calculation indigo) */
.sechead {{display: flex; align-items: center; gap: 10px; font-weight: 650; font-size: 1.1rem; line-height: 1.3;
  margin: 0 0 4px;}}
.sechead .ic {{flex: none; width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center;
  color: var(--tint); background: color-mix(in srgb, var(--tint) 13%, transparent);}}
.sechead .ic .mi {{color: inherit; font-size: 19px;}}
.tint-earth {{--tint: #b7791f;}} .tint-water {{--tint: #0284c7;}} .tint-hx {{--tint: var(--accent);}}
.tint-load {{--tint: #e11d48;}} .tint-limit {{--tint: #6366f1;}} .tint-plain {{--tint: var(--muted);}}
/* the "?" of a section heading right after its name, not at the far end of the card */
div:has(> [data-testid="stMarkdownContainer"] > .sechead) {{display: flex; align-items: center;
  justify-content: flex-start; gap: 8px;}}
[data-testid="stMarkdownContainer"]:has(> .sechead) {{flex: 0 1 auto; width: auto;}}
div[class*="st-key-frow"] {{padding: 0 !important; background: transparent !important;}}
/* a row of fields where a label wraps: every label of the row takes two lines, so the boxes line up */
div[class*="st-key-frow2"] [data-testid="stWidgetLabel"] {{min-height: 2.42rem; display: flex; align-items: flex-end;}}
div[class*="st-key-frow"] [data-testid="stWidgetLabel"] p {{line-height: 1.38; font-size: .875rem;}}
.lbl {{font-weight: 600; font-size: 1.05rem; margin: 10px 0 2px;}}
/* app bar */
.st-key-appbar {{background: var(--bar); color: var(--bar-text); border-radius: 16px; padding: 12px 18px;
  margin-bottom: 4px; gap: 10px;}}
.st-key-appbar p, .st-key-appbar label {{color: var(--bar-text) !important;}}
.st-key-appbar button {{background: rgba(255,255,255,.06); color: var(--bar-text); border-color: rgba(255,255,255,.22);}}
.st-key-appbar button:hover {{border-color: #fff; color: #fff;}}
.st-key-appbar button[data-selected="true"] {{background: #fff !important; color: #13294b !important;
  border-color: #fff !important;}}
.st-key-appbar button[data-selected="true"] p {{color: #13294b !important; font-weight: 600;}}
.logo {{flex: none; width: 38px; height: 38px; border-radius: 10px; display: flex; gap: 5px; justify-content: center;
  align-items: flex-start; padding-top: 9px; background: linear-gradient(180deg, #f97316 0%, #0e7490 100%);}}
.logo i {{display: block; width: 3px; height: 20px; border-radius: 2px; background: #fff;}}
.logo i:nth-child(2) {{height: 24px;}}
.appbrand {{display: flex; align-items: center; gap: 12px; min-width: 0;}}
.appbrand .n {{font-weight: 700; font-size: 1.15rem; line-height: 1.2; color: #fff;}}
.appbrand .s {{font-size: .85rem; color: #94a3b8; line-height: 1.2;}}
/* calculate bar, fixed at the bottom */
.st-key-calcbar {{position: fixed; left: 50%; transform: translateX(-50%); bottom: 12px; z-index: 990;
  width: min(2360px, calc(100vw - 2 * clamp(1rem, 2.5vw, 3.5rem))); background: var(--bar); color: var(--bar-text); border-radius: 16px;
  padding: 10px 14px 10px 18px; box-shadow: 0 8px 30px rgba(15,23,42,.35); gap: 12px;}}
.st-key-calcbar p, .st-key-calcbar span {{color: var(--bar-text);}}
.st-key-calcbar [data-testid="stMarkdownContainer"] p {{margin: 0; font-size: .92rem; line-height: 1.3;}}
.st-key-calcbar button[kind="secondary"] {{background: rgba(255,255,255,.06); color: var(--bar-text);
  border-color: rgba(255,255,255,.22);}}
.st-key-calcbar button[kind="secondary"] p {{color: var(--bar-text);}}
.calcstatus {{font-size: .92rem; line-height: 1.3; color: var(--bar-text);}}
.calcstatus .chip {{margin-right: 6px;}}
/* chips, tiles, answer card, range bars */
/* the switches of the results sheet: wide enough for the labels */
[data-testid="stPopoverBody"]:has(.st-key-sheetpanel) {{min-width: min(1000px, 94vw);}}
.sheethead {{margin: 1.8rem 0 .2rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: 1.35rem;
  scroll-margin-top: 7rem;}}
.sheethead .sechead {{font-size: 1.3rem; margin: 0;}}
.sheethead .sechead .ic {{width: 34px; height: 34px; border-radius: 10px;}} .sheethead .sechead .ic .mi {{font-size: 21px;}}
/* results: the contents bar stays at the top while the sheet scrolls */
.st-key-sheetbar {{position: sticky; top: 3.75rem; z-index: 50; background: color-mix(in srgb, var(--card) 92%, transparent);
  backdrop-filter: blur(6px); border: 1px solid var(--line); border-radius: 12px; padding: 4px 6px 4px 10px;
  box-shadow: var(--shadow); align-items: center;}}
.st-key-sheetbar > div:first-child {{flex: 1 1 0; min-width: 0;}}
.toc {{display: flex; gap: 2px; overflow-x: auto; scrollbar-width: none; white-space: nowrap;}}
.toc::-webkit-scrollbar {{display: none;}}
.toc a {{display: inline-flex; align-items: center; gap: 5px; padding: 5px 10px; border-radius: 8px; font-size: .88rem;
  font-weight: 550; color: var(--text-color, inherit) !important; text-decoration: none !important;}}
.toc a .mi {{font-size: 17px; color: var(--tint);}}
.toc a:hover {{background: color-mix(in srgb, var(--accent) 9%, transparent);}}
#sec-answer {{scroll-margin-top: 7rem;}}
/* results before the first calculation */
.empty {{text-align: center; padding: 40px 16px 14px;}}
.empty .big {{width: 64px; height: 64px; border-radius: 18px; margin: 0 auto 14px; display: grid; place-items: center;
  background: color-mix(in srgb, var(--accent) 12%, transparent);}}
.empty .big .mi {{font-size: 34px;}}
.empty h3 {{margin: 0 0 6px; font-size: 1.35rem;}}
.empty ul {{list-style: none; padding: 0; margin: 14px auto 4px; display: flex; flex-wrap: wrap; gap: 8px;
  justify-content: center; max-width: 720px;}}
.empty li {{display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--card); font-size: .88rem;}}
.empty li .mi {{font-size: 17px;}}
/* design check: counts, then the checks grouped, each with a coloured edge */
.ccounts {{display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 4px 0 10px;}}
.ccount {{background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 12px 16px;
  box-shadow: var(--shadow); display: flex; align-items: center; gap: 12px;}}
.ccount .mi {{font-size: 26px; color: var(--tint); font-variation-settings: "FILL" 1;}}
.ccount .v {{font-size: 1.6rem; font-weight: 750; line-height: 1;}} .ccount .l {{font-size: .85rem; color: var(--muted);}}
.ccount.zero {{opacity: .55;}}
.lv-bad {{--tint: #dc2626;}} .lv-warn {{--tint: #d97706;}} .lv-ok {{--tint: #16a34a;}}
.cgroup {{font-weight: 650; font-size: .95rem; margin: 12px 0 2px; display: flex; align-items: center; gap: 6px;
  color: var(--tint);}}
.cgroup .mi {{color: var(--tint); font-variation-settings: "FILL" 1;}}
div[class*="st-key-chk_bad"], div[class*="st-key-chk_warn"], div[class*="st-key-chk_ok"] {{
  border-left: 4px solid var(--tint) !important; border-radius: 10px;}}
div[class*="st-key-chk_bad"] {{--tint: #dc2626;}} div[class*="st-key-chk_warn"] {{--tint: #d97706;}}
div[class*="st-key-chk_ok"] {{--tint: #16a34a;}}
div[class*="st-key-chk_"] [data-testid="stMarkdownContainer"] p {{margin-bottom: 0;}}
div[class*="st-key-chk_"] {{padding-top: 12px !important; padding-bottom: 12px !important;}}
/* the row under each step: back, where you are, next */
.stepof {{font-size: .85rem; color: var(--muted); white-space: nowrap;}}
.chip {{display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: .78rem; font-weight: 600;
  white-space: nowrap;}}
.chip.ok {{background: #dcfce7; color: #166534;}} .chip.warn {{background: #fef3c7; color: #92400e;}}
.chip.bad {{background: #fee2e2; color: #991b1b;}} .chip.info {{background: #e0f2fe; color: #075985;}}
.chip.grey {{background: rgba(148,163,184,.25); color: inherit;}}
.answer {{display: flex; align-items: center; gap: 22px; background: var(--answer); border: 1px solid var(--line);
  border-radius: 16px; padding: 20px 24px; box-shadow: var(--shadow); margin-bottom: 14px;}}
.answer .mark {{flex: none; width: 76px; height: 76px; border-radius: 50%; display: grid; place-items: center;
  font-size: 40px; color: #fff; font-weight: 700;}}
.answer .mark.ok {{background: #16a34a;}} .answer .mark.bad {{background: #dc2626;}}
.answer .lead {{font-size: .85rem; color: var(--muted);}}
.answer .big {{font-size: 2.1rem; font-weight: 800; line-height: 1.15; margin: 2px 0 4px;}}
.answer .sub {{font-size: 1rem; opacity: .9;}}
.answer .chips {{margin-left: auto; display: flex; flex-direction: column; gap: 6px; align-items: flex-end;}}
.tiles {{display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 16px;}}
.tile {{background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 14px 16px;
  box-shadow: var(--shadow);}}
.tile .l {{font-size: .85rem; color: var(--muted); display: flex; align-items: center; gap: 6px;}}
.mi {{font-family: "Material Symbols Rounded"; font-weight: normal; font-style: normal; font-size: 1.15em;
  line-height: 1; letter-spacing: normal; text-transform: none; white-space: nowrap; direction: ltr;
  -webkit-font-feature-settings: "liga"; font-feature-settings: "liga"; -webkit-font-smoothing: antialiased;
  color: var(--accent); flex: none;}}
.tile .v {{font-size: 1.55rem; font-weight: 700; margin-top: 2px; white-space: nowrap;}}
.tile .d {{font-size: .8rem; color: var(--muted); margin-top: 2px;}}
.tile .v.cold {{color: var(--cold);}} .tile .v.warm {{color: var(--warm);}}
.fignum {{font-size: .78rem; font-weight: 700; color: var(--muted); letter-spacing: .05em; text-transform: uppercase;}}
.figtitle {{font-weight: 600; font-size: .98rem; line-height: 1.3; margin-top: 1px;}}
div[class*="st-key-fighead"] {{align-items: flex-start; flex-wrap: nowrap;}}
div[class*="st-key-fighead"] > div:first-child {{flex: 1 1 0; min-width: 0;}}
div[class*="st-key-fighead"] [data-testid="stMarkdownContainer"] p {{margin: 0;}}
div[class*="st-key-fighead"] button {{min-height: 1.9rem; padding: 0 .6rem;}}
details.more {{font-size: .875rem; color: var(--muted); line-height: 1.45; margin: -4px 0 8px;}}
details.more summary {{cursor: pointer; list-style: none;}}
details.more summary::-webkit-details-marker {{display: none;}}
details.more summary span {{color: var(--accent); font-weight: 600; white-space: nowrap;}}
details.more summary span::after {{content: " ▾";}}
details.more[open] summary span {{display: none;}}
.rangebar {{margin: -6px 0 10px;}}
.rangebar .track {{position: relative; height: 6px; border-radius: 3px; background: var(--track);}}
.rangebar .band {{position: absolute; top: 0; height: 6px; border-radius: 3px; background: var(--band);}}
.rangebar .dot {{position: absolute; top: -4px; width: 14px; height: 14px; margin-left: -7px; border-radius: 50%;
  background: var(--accent); border: 2px solid var(--card); box-shadow: 0 0 0 1px var(--accent);}}
.rangebar .txt {{font-size: .75rem; color: var(--muted); margin-top: 4px; line-height: 1.25;}}
.rangebar .txt.warn {{color: #b45309;}}
/* Matplotlib drawings as SVG: a white sheet (also in dark mode, the drawings use dark ink), centred */
.drawing {{background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 8px; display: flex;
  justify-content: center; box-shadow: inset 0 0 0 4px color-mix(in srgb, var(--accent) 4%, transparent);}}
.drawing img {{display: block;}}
/* the drawing beside the fields stays in view while the fields scroll */
[data-testid="stColumn"]:has(.drawing):not(:has([data-testid="stColumn"])) {{position: sticky; top: 3.8rem;
  align-self: flex-start;}}
{dark_drawing}
.sidenote {{font-size: .78rem; color: var(--muted); margin: -8px 0 10px; line-height: 1.3;}}
.welcome h2 {{text-align: center; font-size: 2rem; margin: 18px 0 4px;}}
.welcome p.lead {{text-align: center; color: var(--muted); margin-bottom: 18px;}}
.choice {{width: 52px; height: 52px; border-radius: 14px; display: grid; place-items: center;
  background: color-mix(in srgb, var(--accent) 12%, transparent);}}
.choice .mi {{font-size: 30px;}}
@media (max-width: 640px) {{
  .block-container {{padding-left: 12px; padding-right: 12px; padding-top: 3rem;}}
  .st-key-appbar {{padding: 10px 12px; border-radius: 12px;}}
  .appbrand .s {{display: none;}}
  .answer {{flex-wrap: wrap; padding: 16px; gap: 12px; align-items: flex-start;}}
  .answer > div:nth-child(2) {{flex: 1 1 200px; min-width: 0;}}
  .answer .mark {{width: 40px; height: 40px; font-size: 22px;}}
  .answer .big {{font-size: 1.35rem;}}
  .answer .chips {{margin-left: 0; flex-direction: row; flex-wrap: wrap; align-items: flex-start;}}
  .tiles {{grid-template-columns: 1fr 1fr; gap: 8px;}}
  .tile {{padding: 10px 12px;}} .tile .v {{font-size: 1.25rem;}}
  .st-key-calcbar {{bottom: 8px; padding: 8px 8px 8px 12px; border-radius: 14px; flex-wrap: nowrap;
    width: calc(100vw - 16px);}}
  .st-key-calcbar > div {{min-width: 0;}}
  .calcstatus {{font-size: .8rem;}}
  .calcstatus .x {{display: none;}}
  .st-key-calcbar button {{padding-left: 10px; padding-right: 10px;}}
  .st-key-open_checks button p, .st-key-calc_goto_error button p {{display: none;}}
  .welcome h2 {{font-size: 1.5rem;}}
  /* tabs: one row of pills that scrolls sideways */
  .st-key-step [role="tablist"] {{flex-wrap: nowrap; gap: 6px; overflow-x: auto !important; scrollbar-width: none;
    width: 100%; padding-bottom: 6px;}}
  .st-key-step [role="tablist"]::-webkit-scrollbar {{display: none;}}
  .st-key-step [role="tablist"] + *, .st-key-step [data-testid="stTabs"] > div:first-child > div:not([role]) {{display: none;}}
  .st-key-step [role="tab"] {{height: auto; padding: 5px 11px; border: 1px solid var(--line); border-radius: 999px;
    margin: 0 !important; flex: none;}}
  .st-key-step [role="tab"] p {{font-size: .85rem;}}
  .st-key-step [role="tab"][aria-selected="true"] {{background: var(--accent); border-color: var(--accent);}}
  .st-key-step [role="tab"][aria-selected="true"] p, .st-key-step [role="tab"][aria-selected="true"]
    [data-testid="stIconMaterial"] {{color: #fff;}}
  .st-key-step [role="tab"][aria-selected="true"] p::after {{color: #fff !important;}}
  /* app bar on one line: the logo, the mode drop-down, the language and the menu */
  .st-key-appbar {{flex-wrap: nowrap;}}
  .appbrand > div:not(.logo) {{display: none;}}
  .st-key-appbar [data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {{width: 116px !important;
    flex: none;}}
  .st-key-appbar [data-testid="stSelectbox"] [data-baseweb="select"] > div {{background: rgba(255,255,255,.08);
    border-color: rgba(255,255,255,.22); color: var(--bar-text);}}
  .st-key-appbar [data-testid="stSelectbox"] svg {{color: var(--bar-text);}}
  .ccounts {{gap: 6px;}} .ccount {{padding: 8px 10px; gap: 8px; flex-direction: column; align-items: flex-start;}}
  .stepof {{display: none;}}
}}
</style>""")


def brand(subtitle: str) -> None:
    st.html(f"<div class='appbrand'>{LOGO}<div><div class='n'>GHEtool &amp; Co.</div>"
            f"<div class='s'>{html.escape(subtitle)}</div></div></div>")


# Section -> (Material icon, tint) of its heading. Unknown sections get a neutral dot.
SECTION_ICONS = {
    "system": ("heat_pump", "hx"), "ground": ("layers", "earth"), "borefield": ("grid_view", "earth"),
    "aquifer": ("water", "water"), "water_quality": ("science", "water"), "wells": ("water_pump", "water"),
    "pipe": ("adjust", "hx"), "fluid": ("water_drop", "hx"), "flow": ("speed", "hx"),
    "load": ("thermostat", "load"), "heat_pump": ("heat_pump", "load"),
    "typical": ("tune", "hx"), "limits": ("device_thermostat", "limit"), "calculation": ("calculate", "limit"), "well_limits": ("rule", "limit"),
    "checks": ("fact_check", "limit"),
    "sp_parcel": ("map", "earth"), "sp_distances": ("straighten", "limit"), "sp_buildings": ("domain", "load"),
    "sp_result": ("pin_drop", "hx"), "sp_wells": ("water_pump", "water"),
}


def section_heading(key: str, label: str) -> str:
    """HTML of a section heading: its icon on a light tint, then the name."""
    name, tint = SECTION_ICONS.get(key, ("radio_button_unchecked", "plain"))
    return (f"<div class='sechead tint-{tint}'><span class='ic'>{icon(name)}</span>"
            f"<span>{html.escape(label)}</span></div>")


# Result section -> (Material icon, tint) of its heading and of its entry in the contents bar
RESULT_ICONS = {
    "answer": ("task_alt", "hx"), "temperatures": ("device_thermostat", "limit"), "energy": ("bolt", "load"),
    "hourly": ("schedule", "limit"), "heat_pump": ("heat_pump", "load"), "hydraulics": ("water_drop", "water"),
    "ground": ("layers", "earth"), "field": ("grid_view", "earth"), "layers": ("stacked_bar_chart", "earth"),
    "load_optimisation": ("balance", "load"), "checks": ("fact_check", "limit"), "export": ("download", "plain"),
}


def sheet_heading(key: str, label: str) -> str:
    """HTML of a heading of the results sheet: its tinted icon, the name, and an anchor for the contents bar."""
    name, tint = RESULT_ICONS.get(key, ("insert_chart", "hx"))
    return (f"<h3 class='sheethead' id='sec-{html.escape(key)}'><div class='sechead tint-{tint}'><span class='ic'>"
            f"{icon(name)}</span><span>{html.escape(label)}</span></div></h3>")


def contents_bar(items: list[tuple[str, str]]) -> None:
    """Links to the sections of the results sheet: (key, label)."""
    links = "".join(f"<a href='#sec-{html.escape(k)}' class='tint-{RESULT_ICONS.get(k, ('', 'hx'))[1]}'>"
                    f"{icon(RESULT_ICONS.get(k, ('insert_chart',))[0])}{html.escape(label)}</a>" for k, label in items)
    st.html(f"<nav class='toc'>{links}</nav>")


def chips(items: list[tuple[str, str]]) -> str:
    """HTML chips; each item is (kind, text) with kind ok, warn, bad, info or grey."""
    return "".join(f"<span class='chip {kind}'>{html.escape(text)}</span>" for kind, text in items)


def answer_card(ok: bool, lead: str, big: str, sub: str, chip_items: list[tuple[str, str]]) -> None:
    st.html(f"<div class='answer'><div class='mark {'ok' if ok else 'bad'}'>{'✓' if ok else '✕'}</div>"
            f"<div><div class='lead'>{html.escape(lead)}</div><div class='big'>{html.escape(big)}</div>"
            f"<div class='sub'>{html.escape(sub)}</div></div><div class='chips'>{chips(chip_items)}</div></div>")


def icon(name: str) -> str:
    """A Material Symbols icon (the same set as the buttons, e.g. "water_drop") for HTML parts of the page."""
    return f"<span class='mi' aria-hidden='true'>{html.escape(name)}</span>"


def _with_icon(label: str) -> str:
    """HTML of a label that may start with an icon written as in Streamlit, ":material/name: text"."""
    found = re.match(r":material/([a-z0-9_]+):\s*(.*)", label, flags=re.S)
    return icon(found.group(1)) + html.escape(found.group(2)) if found else html.escape(label)


def tiles(items: list[tuple[str, str, str, str]]) -> None:
    """Key figures as tiles: (label, value, note, style) with style "", "cold" or "warm". A label may start with
    an icon, ":material/name: "."""
    st.html("<div class='tiles'>" + "".join(
        f"<div class='tile'><div class='l'>{_with_icon(label)}</div><div class='v {style}'>{html.escape(value)}"
        f"</div><div class='d'>{html.escape(note)}</div></div>" for label, value, note, style in items) + "</div>")


def range_bar(value: float, rng: guidance.Typical, low_limit, high_limit, rock: str | None = None) -> None:
    _, _, band_lo, band_hi = guidance.position(value, rng, low_limit, high_limit)
    lo, hi, _, _ = guidance.position(value, rng, low_limit, high_limit)
    dot = (value - lo) / ((hi - lo) or 1.0)
    unusual = guidance.verdict(value, rng) != "typical"
    text = html.escape(guidance.verdict_text(value, rng, rock))
    # the typical range sits in the bar's tooltip; only an unusual value gets a line of text
    st.html(f"<div class='rangebar' title='{text}'><div class='track'><div class='band' style='left:"
            f"{band_lo * 100:.1f}%;width:{(band_hi - band_lo) * 100:.1f}%'></div><div class='dot' style='left:"
            f"{dot * 100:.1f}%'></div></div>" + (f"<div class='txt warn'>{text}</div>" if unusual else "") + "</div>")


def caption(text: str) -> None:
    """A caption that shows its first sentence; the rest opens with "more", so long explanations don't fill the
    page."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ(])", text.strip(), maxsplit=1)
    if len(parts) == 1:
        st.caption(text)
        return
    st.html(f"<details class='more'><summary>{html.escape(parts[0])} <span>{html.escape(t('more'))}</span>"
            f"</summary>{html.escape(parts[1])}</details>")


def side_note(text: str) -> None:
    st.html(f"<div class='sidenote'>{html.escape(text)}</div>")


def calc_status(kind: str, text: str, extra: str = "") -> None:
    """The text at the left of the calculate bar. ``kind`` colours the chip: ok, warn, bad, info or grey."""
    st.html(f"<div class='calcstatus'>{chips([(kind, text)])}<span class='x'>{html.escape(extra)}</span></div>")


def key_table_css() -> None:
    """The compact key tables of the results (``table.keys``)."""
    st.html("""<style>
table.keys {width: 100%; border-collapse: collapse; font-size: 0.92rem; margin: 0;}
table.keys td {border: none; border-bottom: 1px solid rgba(128,128,128,0.18); padding: 6px 4px; vertical-align: top;}
table.keys tr:last-child td {border-bottom: none;}
table.keys td.val {text-align: right; font-weight: 600; white-space: nowrap; padding-left: 12px;}
table.keys .note {font-size: 0.78rem; opacity: 0.65; line-height: 1.25;}
@media (max-width: 640px) {
  table.keys td:first-child {width: 55%;}
  table.keys td.val {white-space: normal; padding-left: 8px;}
}
</style>""")


def expert_css() -> None:
    """Expert: denser inputs, so the two modes look different and more fits on the screen."""
    st.html("""<style>
.stTabs [data-testid="stVerticalBlock"] {gap: .55rem;}
.stTabs [data-testid="stNumberInput"] input {height: 2.1rem; font-size: .9rem;}
.stTabs [data-baseweb="select"] > div {min-height: 2.1rem; font-size: .9rem;}
.stTabs [data-testid="stWidgetLabel"] p {font-size: .82rem;}
.stTabs h5 {font-size: 1rem; line-height: 1.4; padding: .1rem 0 .45rem;}
.stTabs div[class*="st-key-frow"] [data-testid="stWidgetLabel"] p {font-size: .82rem;}
.stTabs div[class*="st-key-frow2"] [data-testid="stWidgetLabel"] {min-height: 2.27rem;}
.stTabs .sechead {font-size: 1rem;} .stTabs .sechead .ic {width: 26px; height: 26px; border-radius: 8px;}
.stTabs .sechead .ic .mi {font-size: 17px;}
.stTabs div[data-testid="stVerticalBlock"][data-test-scroll-behavior] {padding: 10px 14px;}
.rangebar {margin: -4px 0 6px;} .rangebar .txt {font-size: .7rem;}
</style>""")
