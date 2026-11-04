"""Page parts shared by the result views: figures with number and downloads, the compact key table and downloads
made in the page's language."""
from __future__ import annotations

import html
import textwrap

import pandas as pd
import streamlit as st

from .. import i18n, ui
from ..i18n import t


def in_language(fn, *args):
    """For downloads made when the button is clicked: they run outside this page run, so they get the language."""
    lang = i18n.language()
    return lambda: i18n.call_in(lang, fn, *args)


def _fig() -> dict:
    """Figure numbering of this visitor: number of the view . figure in the view (per browser session)."""
    return st.session_state.setdefault("_fig", {"view": 0, "n": 0, "plain": False})


def start_figures(view_number: int) -> None:
    """Called before a view is drawn: its figures are numbered view_number.1, view_number.2, ..."""
    _fig().update(view=view_number, n=0)


def plain_figures(on: bool) -> None:
    """Simple results page: charts with their title, no number and no download menu."""
    _fig()["plain"] = on


def _picture(spec: dict, kind: str) -> bytes:
    import vl_convert as vlc
    return vlc.vegalite_to_png(spec, scale=3) if kind == "png" else vlc.vegalite_to_svg(spec).encode()


def figure(c, caption: str | None = None, data: pd.DataFrame | None = None, width="stretch") -> None:
    """A result chart with its figure number, a caption and downloads: the picture (PNG for reports, SVG to edit) with
    the number, title and caption, and the numbers as CSV. On the page the title stands above the chart as text, so
    it wraps on a phone instead of being cut off."""
    title = c.title if isinstance(c.title, str) else ""
    state = _fig()
    if state["plain"]:
        if title:
            st.markdown(f"<div class='figtitle'>{html.escape(title)}</div>", unsafe_allow_html=True)
        ui.show_chart(c, width, title=not title)
        if caption:
            ui.caption(caption)
        return
    state["n"] += 1
    number = f"{state['view']}.{state['n']}" if state["view"] else str(state["n"])
    head = st.container(horizontal=True, gap="small", key=f"fighead.{number}")
    head.markdown(f"<span class='fignum'>{html.escape(t('Figure {n}', n=number))}</span>"
                  + (f"<div class='figtitle'>{html.escape(title)}</div>" if title else ""), unsafe_allow_html=True)
    stem = "".join(ch if ch.isalnum() else "_" for ch in title)[:50].strip("_") or "figure"
    stem = f"figure_{number.replace('.', '-')}_{stem}"

    def spec():  # made only when a download is clicked
        out = c.to_dict(validate=False)
        out["config"] = {**out.get("config", {}), **i18n.chart_config(background="white").to_dict(validate=False)}
        out.setdefault("width", 860)
        out["title"] = {"text": t("Figure {n}", n=number) + (f" · {title}" if title else ""),
                        "subtitle": textwrap.wrap(caption or "", 120) or "", "subtitleFontSize": 11,
                        "anchor": "start"}
        return out

    with head.popover(t("Download"), icon=":material/download:", width="content"):
        st.download_button(t("Picture for reports (PNG)"), in_language(lambda: _picture(spec(), "png")),
                           f"{stem}.png", "image/png", icon=":material/image:", width="stretch",
                           key=f"fig.{number}.png", on_click="ignore")
        st.download_button(t("Vector graphic (SVG)"), in_language(lambda: _picture(spec(), "svg")),
                           f"{stem}.svg", "image/svg+xml", icon=":material/draw:", width="stretch",
                           key=f"fig.{number}.svg", on_click="ignore")
        if data is not None:
            st.download_button(t("The numbers (CSV)"), in_language(lambda: data.to_csv(index=False).encode()),
                               f"{stem}.csv", "text/csv", icon=":material/table:", width="stretch",
                               key=f"fig.{number}.csv", on_click="ignore")
    ui.show_chart(c, width, title=not title)
    if caption:
        ui.caption(caption)


def key_table(rows: list[tuple[str, str, str]]) -> None:
    """A compact two-column table: item with its note underneath, and the value."""
    body = "".join(
        f"<tr><td>{html.escape(label)}<div class='note'>{html.escape(note)}</div></td>"
        f"<td class='val'>{html.escape(value)}</td></tr>" for label, value, note in rows)
    st.markdown(f"<table class='keys'>{body}</table>", unsafe_allow_html=True)


def TEMPERATURE_CAPTION() -> str:  # noqa: N802 (a text in the current language)
    return t("Blue: the fluid at the heating peaks, the coldest. Red: at the cooling peaks, the warmest. Grey: without "
             "peaks. Brown: the borehole wall. Dashed: your limits. Move the pointer over the chart for the exact "
             "values.")
