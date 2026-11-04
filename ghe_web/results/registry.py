"""The result views of the borehole heat exchanger results, as plug-ins.

A view is one entry in the "View" drop-down of 📊 Results. It registers itself with ``register(ResultView(...))``
in its own module, like the input sections in ``ghe_web/properties``; the page only lists what is registered. To add
a view: write a module with ``render(ctx)``, register it, and import the module in ``ghe_web/results/__init__.py``
(or in your feature package, see ``ghe_web/materials``).

A view gets everything through ``ctx`` (the sized result, its inputs, the project name, ...). It runs as a Streamlit
fragment: a click inside the view redraws only the view, not the whole page. Views that send the user to another tab
set ``fragment=False``.

Settings a view wants saved in the project file go in ``plugin_data(key)``: a dict per view that is stored with the
project (not part of the inputs, so changing it does not make the result out of date).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import pandas as pd
import streamlit as st

from ..i18n import t


@dataclass
class Ctx:
    """What a result view can use."""
    result: Any  # model.SizingResult
    key: Any  # analysis.KeyResults
    sized_inputs: dict  # the inputs the result was calculated with
    sized_json: str  # the same as project JSON (cache key)
    current_json: str  # the inputs on the page now (may differ from sized_json)
    inputs: dict  # the inputs on the page now
    name: str  # project name
    simple: bool  # Simple mode
    found_checks: list = field(default_factory=list)
    show_design_check: Callable[[list], None] = lambda found: None
    project_json: Callable[[], str] = lambda: ""

    @property
    def limits(self) -> dict:
        return self.sized_inputs["limits"].values

    @property
    def stem(self) -> str:
        return self.name.strip() or "ghetool-project"


@dataclass(frozen=True)
class ResultView:
    key: str  # stable id, used in session state and links
    title: str  # English; shown translated
    order: int  # position in the drop-down
    render: Callable[[Ctx], None]
    available: Callable[[Ctx], bool] = lambda ctx: True
    tables: Callable[[Ctx], dict[str, pd.DataFrame]] | None = None  # extra sheets for the Excel workbook and zip
    fragment: bool = True
    on_sheet: bool = True  # a section of the results sheet; False: drawn elsewhere (Further analysis, downloads)


_VIEWS: dict[str, ResultView] = {}


def register(view: ResultView) -> ResultView:
    if view.key in _VIEWS:
        raise ValueError(f"Result view '{view.key}' is already registered.")
    _VIEWS[view.key] = view
    return view


def all_views() -> list[ResultView]:
    return sorted(_VIEWS.values(), key=lambda v: v.order)


def views(ctx: Ctx) -> list[ResultView]:
    """The views that apply to this result, in drop-down order."""
    return [v for v in all_views() if v.available(ctx)]


def sheet_views(ctx: Ctx) -> list[ResultView]:
    """The sections of the results sheet for this result, in page order."""
    return [v for v in views(ctx) if v.on_sheet]


def hidden(ctx: Ctx) -> bool:
    """For views kept in the code but not shown for now (they keep their tests and translations)."""
    return False


def get(key: str) -> ResultView:
    return _VIEWS[key]


def extra_tables(ctx: Ctx) -> dict[str, pd.DataFrame]:
    """Tables of all views for the export (analysis the user ran, the material list, ...)."""
    out: dict[str, pd.DataFrame] = {}
    for view in views(ctx):
        if view.tables is not None:
            out.update(view.tables(ctx))
    return out


# ---------------------------------------------------------------- settings saved with the project

def plugin_store() -> dict:
    """The settings of all views of this visitor, {view key: dict}. Always the same dict object (changed in place), so
    a download made later, outside the page run, sees the settings as they are then."""
    return st.session_state.setdefault("plugin_data", {})


def plugin_data(key: str) -> dict:
    """The saved settings of one view (a dict that is written to the project file)."""
    return plugin_store().setdefault(key, {})


def load_plugin_data(data: dict | None) -> None:
    """After opening a project: its saved view settings replace the current ones."""
    store = plugin_store()
    store.clear()
    store.update({k: dict(v) for k, v in (data or {}).items() if isinstance(v, dict)})


# ---------------------------------------------------------------- drawing

@st.fragment
def _as_fragment(key: str, ctx: Ctx) -> None:
    from .common import start_figures
    start_figures(st.session_state.get("_view_number", 0))
    get(key).render(ctx)


def render(view: ResultView, ctx: Ctx, number: int) -> None:
    """Draws one view, as a fragment unless the view says otherwise. ``number`` is its figure number prefix."""
    from .common import start_figures
    st.session_state._view_number = number
    if view.fragment:
        _as_fragment(view.key, ctx)
    else:
        start_figures(number)
        view.render(ctx)


def title(view: ResultView) -> str:
    return t(view.title)
