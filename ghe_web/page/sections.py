"""The input sections inside the steps: one box per section with its input method, fields and drawing, the
"Typical values" card of Simple mode, and the notes that need several sections."""
from __future__ import annotations

import streamlit as st

from ghe_web.core import model
from ghe_web.i18n import t
from ghe_web.inputs import SectionInput
from ghe_web.inputs import registry as input_registry
from ghe_web.page import guidance, steps
from ghe_web.page.fields import (cached_drawing, field_grid, hourly_input, monthly_table, points_input,
                                 preset_pickers, show_drawing)
from ghe_web.page.state import Page
from ghe_web.strata import page as strata_page
from ghe_web.charts import input_drawings

# Input methods for specialists: listed in Expert only (and in Simple while a project uses them)
EXPERT_ONLY = {("load", "monthly"), ("load", "hourly_building"), ("heat_pump", "curve"), ("pipe", "coaxial"),
               ("pipe", "constant_rb")}


def borehole_depth(page: Page) -> tuple[float, float]:
    """Borehole length and buried depth as currently entered (the borefield section may come later on the page),
    for sections that need them before it is read. For wells: the aquifer bottom, from the surface."""
    if page.system == "open":
        chosen = page.start.get("aquifer") or SectionInput("unconfined", {})
        variant = st.session_state.get(f"{page.gen}.aquifer.variant_key", chosen.variant)
        defaults = {**input_registry.get("aquifer").variant(variant).defaults(),
                    **(chosen.values if variant == chosen.variant else {})}
        return float(st.session_state.get(f"{page.gen}.aquifer.{variant}.bottom", defaults["bottom"])), 0.0
    chosen = page.start.get("borefield") or SectionInput("rectangular", {})
    section = input_registry.get("borefield")
    variant = st.session_state.get(f"{page.gen}.borefield.variant_key", chosen.variant)
    defaults = {**section.variant(variant).defaults(), **(chosen.values if variant == chosen.variant else {})}
    return (float(st.session_state.get(f"{page.gen}.borefield.{variant}.H", defaults["H"])),
            float(st.session_state.get(f"{page.gen}.borefield.{variant}.D", defaults["D"])))


def variant_choices(page: Page, section, chosen: str) -> list[str]:
    """The input methods listed for a section: all in Expert; in Simple the specialist ones only while in use."""
    current = st.session_state.get(f"{page.gen}.{section.key}.variant_key", chosen)
    return [v.key for v in section.variants if not page.simple or (section.key, v.key) not in EXPERT_ONLY
            or v.key in (chosen, current)]


def hidden_in_simple(page: Page, section) -> bool:
    """Simple mode leaves out a section with nothing to choose: one input method and no fields (the heat pump
    efficiency with the SCOP/SEER of the building demand)."""
    chosen = page.start.get(section.key) or SectionInput(section.variant().key, {})
    keys = variant_choices(page, section, chosen.variant)
    return page.simple and len(keys) == 1 and not section.variant(keys[0]).properties


def section_inputs(page: Page, section) -> tuple[SectionInput, object]:
    """Draws one section and returns its values and where its drawing goes (or None)."""
    with st.container(border=True):
        chosen = page.start.get(section.key) or SectionInput(section.variant().key, section.variant().defaults())
        variant = section.variant(chosen.variant)
        # descriptions sit behind the question marks, so the page shows the fields only
        about = t(section.help) if section.help else None
        keys = variant_choices(page, section, variant.key)
        if len(keys) == 1 and section.variant(keys[0]).help:
            about = " ".join(x for x in (about, t(section.variant(keys[0]).help)) if x)
        st.markdown(f"##### {t(section.label)}", help=about)
        if len(keys) > 1:  # the section heading names it, so the drop-down has no label of its own
            shown = section.variant(st.session_state.get(f"{page.gen}.{section.key}.variant_key", variant.key))
            picked = st.selectbox(t(section.label), keys, index=keys.index(variant.key),
                                  format_func=lambda k: t(section.variant(k).label),
                                  key=f"{page.gen}.{section.key}.variant_key", label_visibility="collapsed",
                                  help=t(shown.help) if shown.help else None)
            variant = section.variant(picked)
        elif keys[0] != variant.key:
            variant = section.variant(keys[0])
        values = variant.defaults()
        if variant.key == chosen.variant:
            values.update(chosen.values)
        simple = [p for p in variant.properties if p.kind not in ("monthly", "points", "hourly", "layers")
                  and not (page.simple and (section.key, p.key) in guidance.SIMPLE_HIDDEN)]
        layer_props = [p for p in variant.properties if p.kind == "layers"]
        point_props = [p for p in variant.properties if p.kind == "points"]
        hourly_props = [p for p in variant.properties if p.kind == "hourly"]
        monthly = [p for p in variant.properties if p.kind == "monthly"]
        # wide inputs (tables, hourly files) get their drawing below instead of beside them
        has_drawing = (section.key, variant.key) in input_drawings.DRAWINGS
        side = has_drawing and not monthly and not hourly_props
        form_col, drawing_col = st.columns([3, 2], gap="large") if side else (st.container(), None)
        prefix = f"{page.gen}.{section.key}.{variant.key}"
        with form_col:
            preset_pickers(variant, prefix, values)
            for prop in hourly_props:
                values[prop.key] = hourly_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            for prop in point_props:
                values[prop.key] = points_input(prop, values[prop.key], f"{prefix}.{prop.key}")
            # Simple mode: specialist fields under "More options" (still read and used); Expert: all in line.
            # Simple: fields a drop-down fills in (rock type, pipe, grout, ...) go under "More options" too
            filled = {k for group in variant.presets for option in group.options.values() for k in option}
            basic = [p for p in simple if not page.simple or not (guidance.is_advanced(section.key, p.key) or
                                                              p.key in filled)]
            more = [p for p in simple if p not in basic]
            field_grid(basic, values, prefix, (2 if side else 3) if page.simple else (3 if side else 4))
            if more:
                with st.expander(t("More options ({n})", n=len(more)), icon=":material/tune:"):
                    st.caption(t("Fields most people leave at their typical value. They are always part of the "
                                 "calculation; switch to Expert at the top to see every field at once."))
                    field_grid(more, values, prefix, 2 if side else 3)
            if monthly:
                values.update(monthly_table(monthly, values, f"{prefix}.monthly"))
        for prop in layer_props:  # full width below the fields and the drawing
            values[prop.key] = strata_page.layers_input(prop, values[prop.key], f"{prefix}.{prop.key}", prefix,
                                                        *borehole_depth(page))
        problems = variant.validate(values)
        for msg in problems:
            st.error(msg, icon=":material/error:")
        if not problems:
            for msg in variant.check_warnings(values):
                st.warning(msg, icon=":material/warning:")
        page.notes[section.key] = st.empty()  # filled once all sections are read (warnings that need other sections)
        target = drawing_col if side else (st.container() if has_drawing else None)
    return SectionInput(variant.key, values), target


def read_section(page: Page, section, step: str) -> None:
    page.inputs[section.key], target = section_inputs(page, section)
    page.section_step[section.key] = step
    # Drawn later because some drawings use other sections too
    # (the borehole picture needs the radius from "Borefield").
    if target is not None:
        page.pending_drawings.append((target, section.key, page.inputs[section.key].variant))


def typical_summary(page: Page, sections) -> str:
    """One line per section: the input method, the drop-down choices and the main values."""
    lines = []
    for section in sections:
        chosen = page.inputs[section.key]
        variant = section.variant(chosen.variant)
        prefix = f"{page.gen}.{section.key}.{variant.key}"
        parts = [t(variant.label)] if len(section.variants) > 1 else []
        filled = set()
        for group in variant.presets:
            pick = st.session_state.get(f"{prefix}.preset.{group.label}")
            if pick:
                parts.append(t(pick))
                filled |= {k for k in group.options[pick]}
        for prop in variant.properties:
            if prop.kind in ("float", "int", "choice") and prop.key not in filled and \
                    not guidance.is_advanced(section.key, prop.key) and len(parts) < 5:
                value = chosen.values.get(prop.key)
                if prop.kind == "choice":
                    parts.append(t(str(value)))
                else:
                    parts.append(f"{t(prop.label)} {value:g}" + (f" {t(prop.unit)}" if prop.unit
                                                                                   else ""))
        lines.append(f"**{t(section.label)}:** " + " · ".join(parts))
    return "  \n".join(lines)


def read_steps(page: Page, grouped: dict[str, list]) -> None:
    """Draws every input step and reads its sections into ``page.inputs``."""
    for step, sections in grouped.items():
        with page.step_tabs[step]:
            if step == page.steps["Site"] and "site_plan_done" in st.session_state:
                st.success(t("Borefield set to an irregular field with the {n} positions from the site plan.",
                             n=st.session_state.pop("site_plan_done")), icon=":material/check_circle:")
            if step == page.steps["Borehole"] and "well_plan_done" in st.session_state:
                st.success(t("Wells set from the site plan: {p} production and {i} injection well(s), {d:.0f} m apart, "
                             "{b:.0f} m to the parcel border downstream.", **st.session_state.pop("well_plan_done")),
                           icon=":material/check_circle:")
            # Simple: the calculation method stays asked; the borehole, fluid and limits go in the typical values card
            typical = [x for x in sections if page.simple and x.group in ("Borehole", "Design") and x.key != "calculation"]
            for section in [x for x in sections if x not in typical]:
                if hidden_in_simple(page, section):
                    chosen = page.start.get(section.key)
                    key_ = variant_choices(page, section, chosen.variant if chosen else section.variant().key)[0]
                    page.inputs[section.key] = SectionInput(key_, chosen.values if chosen and chosen.variant == key_
                                                       else section.variant(key_).defaults())
                    continue
                read_section(page, section, step)
            if typical:  # Simple: one card with typical values, opened to change them
                st.markdown("##### " + t("Typical values"), help=t(
                    "These inputs start with values that suit most projects. Open the card to change them; Expert at the "
                    "top shows them as steps of their own."))
                summary_slot = st.empty()
                with st.expander(t("Change the typical values"), icon=":material/tune:"):
                    for section in typical:
                        read_section(page, section, step)
                page.typical_cards.append((summary_slot, typical))
            steps.next_step_button(page, step)

    for key, chosen in page.start.items():  # keep the inputs of the other heat source in the project file
        page.inputs.setdefault(key, chosen)
    page.errors = model.validate(page.inputs)
    page.cross = model.cross_warnings(page.inputs)
    for section_key, msgs in page.cross.items():
        with page.notes[section_key].container():
            for msg in msgs:
                st.info(msg, icon=":material/info:")



def aquifer_from_layers(page: Page) -> None:
    """Under Aquifer: the permeable layers below the groundwater in the layer table of Ground, with a button that
    copies their depth, kf and porosity."""
    from ghe_web.wells.aquifer import from_layers
    rows = list((page.inputs["ground"].values.get("layers") or {}).get("rows") or ())
    chosen = page.inputs["aquifer"]
    guess = from_layers(rows, chosen.values["water_depth"]) if rows else None
    if guess is None or "aquifer" in page.cross:
        return
    prefix = f"{page.gen}.aquifer.{chosen.variant}"
    new = {"bottom": round(guess.bottom, 1), "kf": float(f"{guess.kf:.1e}"), "porosity": round(guess.porosity, 2)}
    if chosen.variant == "confined":
        new["top"] = round(guess.top, 1)
    if all(abs(chosen.values[k] - v) < 1e-9 for k, v in new.items()):
        return
    with page.notes["aquifer"].container():
        st.info(t("The layer table under Ground has a permeable stretch ({rocks}) from {top:.1f} to {bottom:.1f} m "
                  "below ground, kf about {kf:.1e} m/s (typical values for these rocks).",
                  rocks=", ".join(t(r) for r in guess.rocks), top=guess.top, bottom=guess.bottom, kf=guess.kf),
                icon=":material/layers:")
        st.button(t("Use these values"), key=f"{prefix}.from_layers", icon=":material/download:",
                  on_click=lambda: st.session_state.update({f"{prefix}.{k}": v for k, v in new.items()}))


def finish(page: Page) -> None:
    """Once every section is read: the aquifer from the layer table (wells), the project file of the inputs, the
    summaries of the typical values and the input drawings."""
    if page.system == "open":
        aquifer_from_layers(page)
    page.current_json = model.to_json(page.inputs)
    for slot, sections in page.typical_cards:
        with slot.container(border=True):
            st.markdown(typical_summary(page, sections))
    for target, section_key, variant_key in page.pending_drawings:
        if section_key in page.errors or "borefield" in page.errors:
            continue
        with target:  # always visible, in both modes
            show_drawing(cached_drawing(section_key, variant_key, page.current_json, page.lang))

