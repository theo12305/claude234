"""The start page: an optional address and the choice of the heat source. And the short intro above the steps."""
from __future__ import annotations

import html

import streamlit as st

from ghe_web.core import model
from ghe_web.i18n import t
from ghe_web.inputs import SectionInput
from ghe_web.inputs import registry as input_registry
from ghe_web.page import guidance, look
from ghe_web.page.state import Page
from ghe_web.siteplan import page as siteplan_page


def choose_heat_source(page: Page, choice: str, hit: dict | None = None) -> None:
    """Start with this heat source. Like opening a project, so every widget starts from the stored inputs. With an
    address found on the start page, the site plan opens and loads the parcel there."""
    _, inputs_now = st.session_state.project
    inputs_now = {**inputs_now, "system": SectionInput(choice, {})}
    if st.session_state.get("ui_mode", "simple") != "expert" and inputs_now["load"].variant == "monthly":
        # Simple asks about the building (heat per year, peak, cooling), not the monthly ground load
        building = input_registry.get("load").variant("annual_building")
        inputs_now["load"] = SectionInput(building.key, building.defaults())
    st.session_state.project = (st.session_state.get(f"{page.gen}.name", page.project_name), inputs_now)
    st.session_state.generation += 1
    st.session_state.welcomed = True
    if hit is not None:
        siteplan_page.start_from_address(st.session_state.get("welcome.address", "").strip() or hit["label"], hit)
        st.session_state.goto_step = "site_plan"
    else:
        st.session_state.goto_step = "Site"


def welcome_address() -> dict | None:
    """The optional address on the start page; the place picked from the matches, or None."""
    with st.container(border=True):
        st.markdown("#### :material/location_on: " + t("Where is the site? (optional)"))
        st.caption(t("With an address the site plan opens with the parcel, the buildings and the distances of the "
                     "state, places the boreholes or wells, and the ground layers can be predicted for this place. "
                     "Leave it empty to enter the values yourself."))
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        query = c1.text_input(t("Address"), placeholder=t("e.g. Hauptstraße 5, 52062 Aachen"), key="welcome.address")
        if c2.button(t("Find"), key="welcome.find", width="stretch", icon=":material/search:") and query.strip():
            with st.spinner(t("Searching the address...")):
                st.session_state["welcome.hits"] = siteplan_page.geocode(query.strip())
        hits = st.session_state.get("welcome.hits")
        if hits == []:
            st.warning(t("No address found. Try without the house number, or start without an address and find the "
                         "parcel in step ⓪ Site plan."), icon=":material/warning:")
        if not hits or not query.strip():
            return None
        labels = [h["label"] for h in hits]
        pick = st.selectbox(t("Matching places"), labels, key="welcome.pick") if len(hits) > 1 else labels[0]
        st.success(t("**{place}** – now choose the heat source below.", place=pick), icon=":material/location_on:")
        return hits[labels.index(pick)]


def welcome(page: Page) -> None:
    """The start page, shown until a heat source is chosen (or a project opened). Stops the page there."""
    if not st.session_state.get("welcomed", page.gen > 0):
        with st.container(key="welcome"):
            st.html(f"<div class='welcome'><h2>{html.escape(t('Size a geothermal system in your browser'))}</h2>"
                    f"<p class='lead'>{html.escape(t('Free and without login. Your project stays on your device.'))}"
                    f"</p></div>")
            hit = welcome_address()
            st.markdown(f"<div style='text-align:center' class='lbl'>{html.escape(t('Which heat source?'))}</div>",
                        unsafe_allow_html=True)
            for col, (key_, (icon, label, text_)) in zip(st.columns(2, gap="medium"), guidance.HEAT_SOURCES.items()):
                with col, st.container(border=True):
                    st.html(f"<div class='choice'>{look.icon(icon)}</div>")
                    st.markdown(f"#### {t(label)}")
                    st.caption(t(text_))
                    st.button(t("Start with {what} at this address", what=t(label)) if hit else
                              t("Start with {what}", what=t(label)), key=f"welcome.{key_}", width="stretch",
                              type="primary" if key_ == model.system(page.start) else "secondary",
                              on_click=choose_heat_source, args=(page, key_, hit), icon=":material/arrow_forward:")
            st.caption(t("You can switch later in the menu ☰ or under ① in the heat source section. To continue a "
                         "saved project, open it in the menu ☰."))
        st.stop()


def intro(page: Page) -> None:
    """One line above the first steps, and the notes after opening a share link."""
    if st.session_state.get("step") not in (None, page.steps["site_plan"], page.steps["Site"]):
        pass  # the intro only on the first steps
    elif page.system == "open":
        st.caption(t("Fill in the input steps, then press **Size the wells** in the bar at the bottom. Every field "
                     "has a question mark with an explanation; the drop-downs fill in typical values."))
    else:
        st.caption(t("Fill in the input steps, then press **Size borefield** in the bar at the bottom. Every field "
                     "has a question mark with an explanation; the drop-downs fill in typical values."))
    if st.session_state.pop("opened_link", False):
        st.success(t("Opened the project from the link. Hourly demand files are not part of links: upload it again if "
                     "the project uses one."), icon=":material/link:")
    if st.session_state.pop("link_error", False):
        st.error(t("This link does not contain a readable project. Ask for a new link or the project file."),
                 icon=":material/link_off:")
