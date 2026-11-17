"""The ⓪ Site plan step (ghe_web/siteplan) and what it hands to the inputs: borehole positions for an irregular
borefield, or the numbers, distance and flow direction of groundwater wells."""
from __future__ import annotations

import math

import streamlit as st

from ghe_web.inputs import SectionInput
from ghe_web.inputs import registry as input_registry
from ghe_web.page import steps
from ghe_web.page.state import Page
from ghe_web.siteplan import page as siteplan_page
from ghe_web.wells import page as wells_page


def use_site_plan(points) -> None:
    """Called from the site plan: the borefield becomes an irregular field with these positions."""
    st.session_state.site_plan_points = points
    st.rerun()


def apply_site_plan(page: Page) -> None:
    """After "Use in the sizing" on the site plan: the borefield becomes an irregular field with its positions."""
    if "site_plan_points" in st.session_state:
        pts = st.session_state.pop("site_plan_points")
        x0, y0 = min(x for x, _ in pts), min(y for _, y in pts)
        borefield = page.inputs["borefield"]
        values = dict(borefield.values) if borefield.variant == "custom" else \
            {**input_registry.get("borefield").variant("custom").defaults(),
             **{k: v for k, v in borefield.values.items() if k in ("H", "D", "r_b_mm")}}
        values["points"] = tuple((round(x - x0, 2), round(y - y0, 2)) for x, y in pts)
        st.session_state.site_plan_origin = ((x0, y0), values["points"])  # the material list plan draws the buildings
        st.session_state.project = (page.name, {**page.inputs, "borefield": SectionInput("custom", values)})
        st.session_state.generation += 1
        st.session_state.goto_step = "Site"
        st.session_state.site_plan_done = len(pts)
        st.rerun()



def use_well_plan(placement, direction: float) -> None:
    """Called from the site plan for groundwater wells: numbers, distance, border distance and flow direction."""
    st.session_state.well_plan = (placement, direction)
    st.rerun()


def apply_well_plan(page: Page) -> None:
    """After "Use in the sizing" for wells: numbers, distance, border distance and flow direction."""
    if "well_plan" in st.session_state:
        placement, direction = st.session_state.pop("well_plan")
        w = page.inputs["wells"]
        values = {**w.values, "border": float(placement.border_downstream), "orientation": "Injection downstream"}
        if len(placement.production) > 1 or len(placement.injection) > 1:
            spacings = [math.dist(a, b) for group in (placement.production, placement.injection)
                        for a, b in zip(group, group[1:])]
            values["spacing"] = round(min(spacings), 1)
        if w.variant == "check":
            values.update(n_production=len(placement.production), n_injection=len(placement.injection),
                          distance=float(placement.distance))
        else:
            values["max_distance"] = float(placement.distance)
        aquifer_input = page.inputs["aquifer"]
        st.session_state.project = (page.name, {**page.inputs, "wells": SectionInput(w.variant, values),
                                           "aquifer": SectionInput(aquifer_input.variant,
                                                                   {**aquifer_input.values, "direction": direction})})
        st.session_state.generation += 1
        st.session_state.goto_step = "Borehole"
        st.session_state.well_plan_done = {"p": len(placement.production), "i": len(placement.injection),
                                           "d": placement.distance, "b": placement.border_downstream}
        st.rerun()


def well_plan_defaults(page: Page) -> dict:
    """What the site plan starts from for wells: the flow direction, the spacing and the numbers of wells (given, or
    from the last sizing)."""
    w = page.inputs["wells"].values
    n_p, n_i = w.get("n_production", 1), w.get("n_injection", 1)
    if page.inputs["wells"].variant == "size" and "result_json" in st.session_state:
        try:
            d = wells_page.cached_design(st.session_state.result_json)
            n_p, n_i = d.n_production, d.n_injection
        except Exception:
            pass
    return {"direction": page.inputs["aquifer"].values["direction"], "spacing": w["spacing"], "n_production": n_p,
            "n_injection": n_i}


@st.fragment
def site_plan(page: Page) -> None:
    """The site plan as a fragment: a click on the map or a changed distance redraws only the site plan, not the
    input steps and results. Loading a parcel and using the positions rerun the whole page."""
    if page.system == "open":
        siteplan_page.page(use_well_plan, well_plan_defaults(page))
    else:
        siteplan_page.page(use_site_plan)


def tab(page: Page) -> None:
    """The site plan tab. Only drawn while open: the map and the data services are slow."""
    with page.step_tabs[page.steps["site_plan"]]:
        # Only drawn while open: the map and the data services are slow.
        if st.session_state.get("step") == page.steps["site_plan"]:
            site_plan(page)
        steps.next_step_button(page, page.steps["site_plan"])
