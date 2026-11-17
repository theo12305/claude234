"""The project the widgets start from: the defaults, a project file opened in the menu or a share link. Also the
project file itself, the "Save project" button and the share link."""
from __future__ import annotations

import streamlit as st

from ghe_web import i18n
from ghe_web.core import model
from ghe_web.downloads import share_link
from ghe_web.i18n import t
from ghe_web.page.state import Page
from ghe_web.results import registry as results_registry
from ghe_web.siteplan import page as siteplan_page


def take_settings(text: str) -> None:
    """After opening a project (file or link): its language, mode, site plan address and result settings, and new
    widgets (a new generation) so every field starts from the project."""
    saved = model.saved_language(text)
    if saved in i18n.LANGUAGES:
        st.session_state.pending_language = saved
    if model.saved_setting(text, "mode") in ("simple", "expert"):
        st.session_state.pending_mode = model.saved_setting(text, "mode")
    siteplan_page.set_address(model.saved_setting(text, "address") or "")
    results_registry.load_plugin_data(model.saved_plugins(text))
    st.session_state.generation += 1


def load() -> tuple[str, dict, int]:
    """The project name and inputs the widgets start from, and the widget generation. Widget keys include the
    generation number, so loading a project rebuilds every widget. A share link (?p=...) is opened once and then
    dropped from the address."""
    if "project" not in st.session_state:
        st.session_state.project = ("", model.default_inputs())
        st.session_state.generation = 0
    if share_link.PARAM in st.query_params:
        packed = st.query_params[share_link.PARAM]
        del st.query_params[share_link.PARAM]
        try:
            text = share_link.decode(packed)
            st.session_state.project = model.from_json(text)
        except Exception:
            st.session_state.link_error = True
        else:
            take_settings(text)
            st.session_state.opened_link = True
        st.rerun()
    project_name, start = st.session_state.project
    return project_name, start, st.session_state.generation


def project_json(page: Page) -> str:
    """The project file: inputs, name, language, Simple/Expert, the address of the site plan and the settings of
    the result views (read when the download is clicked, so settings changed inside a view are included)."""
    return model.to_json(page.inputs, page.name, language=page.lang, mode=page.ui_mode, address=page.address,
                         plugins=page.plugins)



def save_and_share(page: Page) -> None:
    """Fills "Save project" and the share link in the menu, once the inputs are read."""
    with page.save_slot:
        st.download_button(t("Save project"), lambda: project_json(page).encode(),
                           f"{page.name.strip() or 'ghetool-project'}.json", "application/json", width="stretch",
                           icon=":material/save:", on_click="ignore")
    with page.share_slot, st.expander(t("Share link"), icon=":material/link:"):
        link, dropped = share_link.link(st.context.url or "", project_json(page))
        st.markdown(t("**Share this project**"))
        st.caption(t("Anyone with the link opens the site with your inputs filled in. The project is stored in the "
                     "link itself; nothing is saved on the server. Copy it with the button at the right of the box."))
        st.code(link, language=None, wrap_lines=True)
        if dropped:
            st.warning(t("The hourly demand file is not part of the link (too large): send the file separately."),
                       icon=":material/warning:")
        if len(link) > 8000:
            st.caption(t("This link is long ({n:,} characters). Some e-mail programs cut long links; if it does not "
                         "open, send the project file instead.", n=len(link)))


    # ---------------------------------------------------------------- calculation
