"""The bar at the top: the name, Simple/Expert, the language and the menu ☰. No sidebar: phones hide it.
The language is read first, because every text below follows it."""
from __future__ import annotations

import streamlit as st

from ghe_web import i18n
from ghe_web.i18n import t
from ghe_web.page import look

MODES = {"simple": "Simple", "expert": "Expert", "learn": "Learn"}  # Learn: example projects, ghe_web/learn


def draw() -> tuple[str, str, object, object]:
    """Draws the bar. Returns the language, the mode, the slot for the name and the menu popover."""
    if "pending_language" in st.session_state:  # set by opening a project file
        st.session_state.language = st.session_state.pop("pending_language")
    if "pending_mode" in st.session_state:
        st.session_state.ui_mode = st.session_state.pop("pending_mode")
    bar = st.container(key="appbar", horizontal=True, vertical_alignment="center", gap="small")
    with bar:
        brand_slot = st.empty()
        st.space("stretch")
        mode_slot = st.empty()
        lang = st.segmented_control("Language · Sprache", list(i18n.LANGUAGES), format_func=lambda c: c.upper(),
                                    default=i18n.DEFAULT, required=True, key="language", label_visibility="collapsed")
        menu = st.popover("", icon=":material/menu:", help="Menu")
    lang = i18n.set_language(lang)
    if st.session_state.get("shown_language", lang) != lang:
        # The browser sends choices back as their shown label, which is now in the other language, so Streamlit
        # would reset them. Writing the values back first keeps every choice (radios, drop-downs, view switches).
        for k, v in list(st.session_state.items()):
            if k == "language":
                continue
            if isinstance(v, (str, int)) and not isinstance(v, bool) or isinstance(v, list) and v and \
                    all(isinstance(x, (str, int)) for x in v):
                st.session_state[k] = v
    st.session_state.shown_language = lang
    with mode_slot:
        if look.is_phone():  # a drop-down keeps the bar on one line
            st.session_state.setdefault("ui_mode", "simple")
            ui_mode = st.selectbox(t("Mode"), list(MODES), format_func=lambda k: t(MODES[k]), key="ui_mode",
                                   label_visibility="collapsed")
        else:
            ui_mode = st.segmented_control(t("Mode"), list(MODES), format_func=lambda k: t(MODES[k]),
                                           default="simple", required=True, key="ui_mode",
                                           label_visibility="collapsed")
    return lang, ui_mode, brand_slot, menu
