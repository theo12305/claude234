"""The look of the page (Streamlit): colours for light and dark mode, the app bar, the answer card and key tiles of
the results, the range bars next to the inputs and the calculate bar fixed at the bottom of the screen."""
from __future__ import annotations

import html

import streamlit as st

from . import guidance
from .i18n import t

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


def theme() -> str:
    try:
        kind = st.context.theme.type
    except Exception:
        kind = None
    return kind if kind in PALETTE else "light"


def inject_css() -> None:
    c = PALETTE[theme()]
    st.html(f"""<style>
:root {{--card:{c['card']};--line:{c['line']};--muted:{c['muted']};--accent:{c['accent']};--bar:{c['bar']};
  --bar-text:{c['bar_text']};--band:{c['band']};--track:{c['track']};--shadow:{c['shadow']};--cold:{c['cold']};
  --warm:{c['warm']};--answer:{c['answer']};}}
.block-container {{padding-top: 3.2rem; padding-bottom: 8rem; max-width: 1280px;}}
[data-testid="stMetricValue"] {{font-size: 1.6rem;}}
h1, h2, h3, h4, h5 {{letter-spacing: -0.01em;}}
/* cards: containers get the card colour (the bordered ones are the input sections and result boxes) */
div[data-testid="stVerticalBlock"][data-test-scroll-behavior] {{background: var(--card);}}
.st-key-welcome, .st-key-quick_downloads, .st-key-calcbar div[data-testid="stVerticalBlock"],
.st-key-appbar div[data-testid="stVerticalBlock"] {{background: transparent !important;}}
/* tabs: the input steps */
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
  width: min(1240px, calc(100vw - 24px)); background: var(--bar); color: var(--bar-text); border-radius: 16px;
  padding: 10px 14px 10px 18px; box-shadow: 0 8px 30px rgba(15,23,42,.35); gap: 12px;}}
.st-key-calcbar p, .st-key-calcbar span {{color: var(--bar-text);}}
.st-key-calcbar [data-testid="stMarkdownContainer"] p {{margin: 0; font-size: .92rem; line-height: 1.3;}}
.st-key-calcbar button[kind="secondary"] {{background: rgba(255,255,255,.06); color: var(--bar-text);
  border-color: rgba(255,255,255,.22);}}
.st-key-calcbar button[kind="secondary"] p {{color: var(--bar-text);}}
.calcstatus {{font-size: .92rem; line-height: 1.3; color: var(--bar-text);}}
.calcstatus .chip {{margin-right: 6px;}}
/* chips, tiles, answer card, range bars */
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
.tile .l {{font-size: .85rem; color: var(--muted);}}
.tile .v {{font-size: 1.55rem; font-weight: 700; margin-top: 2px; white-space: nowrap;}}
.tile .d {{font-size: .8rem; color: var(--muted); margin-top: 2px;}}
.tile .v.cold {{color: var(--cold);}} .tile .v.warm {{color: var(--warm);}}
.rangebar {{margin: -6px 0 10px;}}
.rangebar .track {{position: relative; height: 6px; border-radius: 3px; background: var(--track);}}
.rangebar .band {{position: absolute; top: 0; height: 6px; border-radius: 3px; background: var(--band);}}
.rangebar .dot {{position: absolute; top: -4px; width: 14px; height: 14px; margin-left: -7px; border-radius: 50%;
  background: var(--accent); border: 2px solid var(--card); box-shadow: 0 0 0 1px var(--accent);}}
.rangebar .txt {{font-size: .75rem; color: var(--muted); margin-top: 4px; line-height: 1.25;}}
.rangebar .txt.warn {{color: #b45309;}}
.sidenote {{font-size: .78rem; color: var(--muted); margin: -8px 0 10px; line-height: 1.3;}}
.welcome h2 {{text-align: center; font-size: 2rem; margin: 18px 0 4px;}}
.welcome p.lead {{text-align: center; color: var(--muted); margin-bottom: 18px;}}
.choice {{font-size: 2.6rem; line-height: 1;}}
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
}}
</style>""")


def brand(subtitle: str) -> None:
    st.html(f"<div class='appbrand'>{LOGO}<div><div class='n'>GHEtool Web</div>"
            f"<div class='s'>{html.escape(subtitle)}</div></div></div>")


def chips(items: list[tuple[str, str]]) -> str:
    """HTML chips; each item is (kind, text) with kind ok, warn, bad, info or grey."""
    return "".join(f"<span class='chip {kind}'>{html.escape(text)}</span>" for kind, text in items)


def answer_card(ok: bool, lead: str, big: str, sub: str, chip_items: list[tuple[str, str]]) -> None:
    st.html(f"<div class='answer'><div class='mark {'ok' if ok else 'bad'}'>{'✓' if ok else '✕'}</div>"
            f"<div><div class='lead'>{html.escape(lead)}</div><div class='big'>{html.escape(big)}</div>"
            f"<div class='sub'>{html.escape(sub)}</div></div><div class='chips'>{chips(chip_items)}</div></div>")


def tiles(items: list[tuple[str, str, str, str]]) -> None:
    """Key figures as tiles: (label, value, note, style) with style "", "cold" or "warm"."""
    st.html("<div class='tiles'>" + "".join(
        f"<div class='tile'><div class='l'>{html.escape(label)}</div><div class='v {style}'>{html.escape(value)}"
        f"</div><div class='d'>{html.escape(note)}</div></div>" for label, value, note, style in items) + "</div>")


def range_bar(value: float, rng: guidance.Typical, low_limit, high_limit, rock: str | None = None) -> None:
    _, _, band_lo, band_hi = guidance.position(value, rng, low_limit, high_limit)
    lo, hi, _, _ = guidance.position(value, rng, low_limit, high_limit)
    dot = (value - lo) / ((hi - lo) or 1.0)
    unusual = guidance.verdict(value, rng) != "typical"
    st.html(f"<div class='rangebar'><div class='track'><div class='band' style='left:{band_lo * 100:.1f}%;"
            f"width:{(band_hi - band_lo) * 100:.1f}%'></div><div class='dot' style='left:{dot * 100:.1f}%'></div>"
            f"</div><div class='txt{' warn' if unusual else ''}'>{html.escape(guidance.verdict_text(value, rng, rock))}"
            f"</div></div>")


def side_note(text: str) -> None:
    st.html(f"<div class='sidenote'>{html.escape(text)}</div>")


def calc_status(kind: str, text: str, extra: str = "") -> None:
    """The text at the left of the calculate bar. ``kind`` colours the chip: ok, warn, bad, info or grey."""
    st.html(f"<div class='calcstatus'>{chips([(kind, text)])}<span class='x'>{html.escape(extra)}</span></div>")
