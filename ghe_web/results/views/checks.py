"""Design check: every input and result check in one list (not a fragment: its buttons open other tabs)."""
from __future__ import annotations

import streamlit as st

from ...i18n import t
from ..registry import Ctx, ResultView, hidden, register


def render(ctx: Ctx) -> None:
    if ctx.sized_json != ctx.current_json:
        st.info(t("This list is for the current inputs; the results for them are not calculated yet."),
                icon=":material/info:")
    ctx.show_design_check(ctx.found_checks)


# The design check is a step of its own before the results now (app.py); the view stays for later use.
register(ResultView("checks", "Design check", 20, render, fragment=False, available=hidden))
