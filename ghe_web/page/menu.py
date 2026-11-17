"""The menu ☰ of the app bar: project name, open and save a project, share link, help and the switch back to the
start page."""
from __future__ import annotations

import streamlit as st

from ghe_web.core import model
from ghe_web.i18n import t
from ghe_web.page import look, project
from ghe_web.page.state import Page
from ghe_web.learn import page as learn_page
from ghe_web.wells import page as wells_page


def draw(page: Page) -> None:
    """The menu. "Save project" and the share link are filled in later (``project.save_and_share``), once the
    inputs are read."""
    with page.menu:
        st.markdown(t("**Project**"))
        page.name = st.text_input(t("Project name"), value=page.project_name, key=f"{page.gen}.name")
        uploaded = st.file_uploader(t("Open a saved project"), type="json", key=f"{page.gen}.upload")
        if uploaded is not None:
            text = uploaded.getvalue().decode()
            try:
                st.session_state.project = model.from_json(text)
            except Exception as exc:
                st.error(t("Could not open this file: {error}", error=exc))
            else:
                project.take_settings(text)
                st.session_state.welcomed = True
                st.rerun()
        page.save_slot = st.empty()  # filled after the inputs are read
        page.share_slot = st.container()
        st.caption(t("Projects are saved as a file on your computer, including the language. Nothing is stored on "
                     "the server."))
        st.divider()
        st.markdown(t("**Help**"))
        with st.expander(t("How to use this tool"), icon=":material/help:"):
            if page.system == "open":
                st.markdown(t(
                    "1. **Site plan** (optional): find the parcel.\n2. **Ground & aquifer**: choose groundwater "
                    "wells as heat source, the ground temperature (or predicted layers), the aquifer and the water "
                    "analysis.\n3. **Wells**: drilling diameter, well losses, and whether to size the wells or "
                    "check given ones.\n4. **Loads**: the heat taken from and put into the groundwater, or the "
                    "building demand.\n5. **Limits & calculation**: temperature spread and the limits of the water "
                    "authority.\n6. Press **Size the wells** in the bar at the bottom. The **:material/bar_chart: "
                    "Results** tab shows the flow, wells, water levels, temperatures, the site map, the well "
                    "construction and the downloads.\n\nThe well hydraulics (Thiem, Dupuit-Jacob, Sichardt) and the "
                    "thermal model (flow paths of the injected water and a planar plume) are written for this tool; "
                    "GHEtool has no open-loop model."))
            else:
                st.markdown(t(
                    "1. **Site plan** (optional): find the parcel and place as many boreholes as fit.\n2. **"
                    "Ground & borefield**: ground properties (or predicted layers) and the borefield layout.\n3. **"
                    "Borehole & fluid**: borehole heat exchanger, heat transfer fluid and flow rate.\n4. **"
                    "Loads**: the heat extracted from and injected into the ground, or the building demand with the "
                    "heat pump efficiency.\n5. **Limits & calculation**: the allowed fluid temperatures, and "
                    "whether to size the length or check a given one.\n6. Press **Size borefield** in the bar at the "
                    "bottom. The **:material/bar_chart: Results** tab shows key figures, charts, further analysis "
                    "and the PDF report and Excel export.\n\nSave the project in the menu ☰ to continue later. "
                    "Calculations use the open-source [GHEtool](https://github.com/wouterpeere/GHEtool)."))
        st.caption(t(":material/dark_mode: Dark mode: menu **⋮** at the top right > **Settings** > theme **Dark**."))
        st.caption(t("Simple / Expert / Learn: the switch next to the language. Simple shows the main fields and "
                     "puts the others under \"More options\"; nothing is left out of the calculation. Learn is Simple "
                     "plus explanations, an introduction, a glossary and the literature."))
        learn_page.menu_button()
        if page.system == "open":
            wells_page.sources_button("menu")
        if st.button(t("Change the heat source"), icon=":material/swap_horiz:", width="stretch",
                     help=t("Opens the start page with the choice between borehole heat exchangers and groundwater "
                            "wells. Your inputs stay.")):
            st.session_state.welcomed = False
            st.rerun()


def brand(page: Page) -> None:
    """The name in the app bar with the subtitle of the heat source."""
    with page.brand_slot:
        look.brand(t("Groundwater well sizing") if page.system == "open" else t("Borehole heat exchanger sizing"))
