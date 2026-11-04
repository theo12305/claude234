"""The results sheet: which parts of 📊 Results are shown and what the temperature charts contain.

Every result view is a section of the sheet that can be switched on and off, and most sections have parts (single
charts, tables) that can be switched too. The temperature charts have their own switches (series, limits, shading,
markers). The choice is stored with the project (``plugin_data("sheet")``) and the PDF report uses the same choice,
so the report looks like the sheet on the screen.

To give a new view parts of its own, add them to ``PARTS`` and ask ``on(part)`` in its ``render``.
"""
from __future__ import annotations

from dataclasses import fields

import streamlit as st

from .. import plots
from ..i18n import t
from .registry import plugin_data

KEY = "sheet"

# Sections switched on when nothing was chosen yet. The slow ones (maps of the ground and of each borehole) start off.
SECTION_DEFAULTS = {"temperatures": True, "energy": True, "hourly": True, "ground": False, "field": False,
                    "layers": True, "load_optimisation": False}

# Parts of the sections: (id, title, on by default)
PARTS: dict[str, list[tuple[str, str, bool]]] = {
    "summary": [("tiles", "Key figures", True), ("key_table", "Table of the key results", False),
                ("warnings", "Warnings", True)],
    "temperatures": [("temp_years", "Fluid temperature over the years", True),
                     ("temp_zoom", "Last year next to it (zoom)", True),
                     ("temp_last", "Last year with supply and return", False),
                     ("temp_extremes", "Lowest and highest temperature per year", True),
                     ("temp_table", "Table of the monthly temperatures", False)],
    "energy": [("energy_balance", "Monthly energy balance of the ground", True),
               ("energy_numbers", "Yearly extraction, injection and imbalance", True),
               ("load_duration", "Load duration curve", True)],
    "hourly": [("hourly_daily", "Hourly fluid temperature (daily range)", True),
               ("hourly_last", "Hourly fluid temperature in the last year", True),
               ("hourly_heatmap", "Heat map of the last year", False)],
    "ground": [("ground_numbers", "Ground key figures", True), ("ground_map", "Ground temperature map", True),
               ("gfunction", "g-function", False)],
}

# The switches of the temperature charts, in the order of plots.ChartStyle
STYLE_LABELS = {"base": "Fluid without peaks (grey)", "peak_heat": "Fluid at the heating peaks (blue)",
                "peak_cool": "Fluid at the cooling peaks (red)", "limits": "Temperature limits (dashed lines)",
                "shading": "Shading outside the limits", "limit_labels": "Labels of the limits",
                "extremes": "Lowest and highest value marked", "pointer": "Values at the pointer"}


def _store() -> dict:
    return plugin_data(KEY)


def section_on(view_key: str) -> bool:
    return bool(_store().get(f"section.{view_key}", SECTION_DEFAULTS.get(view_key, True)))


def on(part: str) -> bool:
    """True when this part of a section is switched on."""
    default = next((d for parts in PARTS.values() for p, _, d in parts if p == part), True)
    return bool(_store().get(part, default))


def style() -> plots.ChartStyle:
    return plots.ChartStyle.from_dict(_store().get("style"))


def choice() -> dict:
    """Everything chosen, with the defaults filled in: {"sections": {view: bool}, "parts": {part: bool},
    "style": ChartStyle}. For the PDF report, which runs outside the page."""
    return {"sections": {k: section_on(k) for k in SECTION_DEFAULTS},
            "parts": {p: on(p) for parts in PARTS.values() for p, _, _ in parts}, "style": style()}


def _toggle(label: str, store_key: str, value: bool, *, style_key: bool = False) -> None:
    gen = st.session_state.get("generation", 0)  # a project opened from a file brings its own choice
    widget = f"{gen}.{KEY}.{store_key}"

    def save():
        if style_key:
            _store().setdefault("style", {})[store_key] = st.session_state[widget]
        else:
            _store()[store_key] = st.session_state[widget]
    st.toggle(label, value=value, key=widget, on_change=save)


def customize(views: list) -> None:
    """The popover with all switches. ``views``: the result views of this result (ResultView), in sheet order."""
    with st.popover(t("Customize the results"), icon=":material/tune:"), st.container(key="sheetpanel"):
        st.caption(t("Choose what the results sheet shows. The PDF report follows the same choice. Saved with the "
                     "project."))
        cols = st.columns(3, gap="medium")
        with cols[0]:
            st.markdown(t("**Sections**"))
            for view in views:
                _toggle(t(view.title), f"section.{view.key}", section_on(view.key))
            st.markdown(t("**Summary**"))
            for part, title, _ in PARTS["summary"]:
                _toggle(t(title), part, on(part))
        with cols[1]:
            st.markdown(t("**Charts and tables**"))
            for view in views:
                parts = PARTS.get(view.key)
                if not parts or not section_on(view.key):
                    continue
                st.caption(t(view.title))
                for part, title, _ in parts:
                    _toggle(t(title), part, on(part))
        with cols[2]:
            st.markdown(t("**Temperature charts**"))
            current = style()
            for f in fields(plots.ChartStyle):
                _toggle(t(STYLE_LABELS[f.name]), f.name, getattr(current, f.name), style_key=True)
        if st.button(t("Back to the standard sheet"), icon=":material/restart_alt:", key="sheet.reset"):
            _store().clear()
            for k in [k for k in st.session_state if f".{KEY}." in str(k)]:
                del st.session_state[k]
            st.rerun()
