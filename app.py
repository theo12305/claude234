"""GHEtool & Co.: the Streamlit page. Start with:  streamlit run app.py

This file is only the frame of the page. It reads from top to bottom like the page itself; every part is a function
in ghe_web/page/ (map: ghe_web/README.md). ``page`` (ghe_web/page/state.py) carries what the parts share.
"""
import pathlib
import sys

import streamlit as st


def _drop_stale_package():
    """After a deploy the server reruns app.py but keeps the old ghe_web modules in memory, which crashes
    the page. When any ghe_web file changed since it was imported, forget the old modules and cached results."""
    files = (pathlib.Path(__file__).parent / "ghe_web").rglob("*.py")
    stamp = tuple(sorted((str(p), p.stat().st_mtime_ns) for p in files))
    loaded = sys.modules.get("ghe_web")
    if loaded is not None and getattr(loaded, "_stamp", None) != stamp:
        for name in [m for m in sys.modules if m == "ghe_web" or m.startswith("ghe_web.")]:
            del sys.modules[name]
        st.cache_data.clear()
        st.cache_resource.clear()
    import ghe_web
    ghe_web._stamp = stamp


_drop_stale_package()

from ghe_web.core import model  # noqa: E402
from ghe_web.learn import page as learn_page  # noqa: E402
from ghe_web.page import (appbar, calculation, design_check, look, menu, project, results_tab,  # noqa: E402
                          sections, site_plan, start, steps)
from ghe_web.page.state import Page  # noqa: E402
from ghe_web.results import registry as results_registry  # noqa: E402
from ghe_web.siteplan import page as siteplan_page  # noqa: E402
from ghe_web.wells import page as wells_page  # noqa: E402

st.set_page_config(page_title="GHEtool & Co.", page_icon=look.favicon(), layout="wide")
look.inject_css()
look.key_table_css()

# App bar: the language first (every text below follows it), Simple/Expert and the menu ☰
lang, ui_mode, brand_slot, menu_popover = appbar.draw()
if ui_mode == "expert":
    look.expert_css()

# The project the widgets start from (defaults, a project file or a share link). The heat source decides the
# sections and tabs; its drop-down is drawn further down, so its value is read here.
project_name, start_inputs, gen = project.load()
system = st.session_state.get(f"{gen}.system.variant_key", model.system(start_inputs))
page = Page(lang=lang, ui_mode=ui_mode, gen=gen, project_name=project_name, start=start_inputs, system=system,
            steps=steps.labels(system, ui_mode != "expert", ui_mode == "learn"), menu=menu_popover, brand_slot=brand_slot)
steps.follow_goto(page)

menu.draw(page)
menu.brand(page)
start.welcome(page)  # the start page stops here until a heat source is chosen
start.intro(page)

# The calculate bar: fixed at the bottom of the screen (CSS), filled once the inputs are read.
page.calc_slot = st.container(key="calcbar", horizontal=True, vertical_alignment="center", gap="small")

# The input steps: every section read into page.inputs
grouped = steps.grouped_sections(page)
steps.make_tabs(page, grouped)
sections.read_steps(page, grouped)
sections.finish(page)

# ⓪ Site plan, and what it hands to the inputs
site_plan.apply_site_plan(page)
site_plan.apply_well_plan(page)
site_plan.tab(page)

# Save project and share link in the menu (now that the inputs are read)
page.address, page.plugins = siteplan_page.address(), results_registry.plugin_store()
project.save_and_share(page)
learn_page.tabs(page)  # Learn mode: introduction, glossary, literature (ghe_web/learn)

if "result_json" in st.session_state and \
        model.system(model.from_json(st.session_state.result_json)[1]) != page.system:
    del st.session_state.result_json  # a result of the other heat source

if page.system == "open":  # groundwater wells: their own calculation, results and calculate bar (ghe_web/wells)
    wells_page.page(page.inputs, page.errors, page.current_json, page.name, page.lang, page.calc_slot,
                    page.step_tabs[page.steps["results"]],
                    lambda key: page.steps[steps.section_step_key(page, key)],
                    lambda key: st.session_state.update(goto_step=steps.section_step_key(page, key)))
    st.stop()

# Borehole heat exchangers: calculate, design check, results
calculation.run_if_requested(page)
found_checks = design_check.design_checks(page)
calculation.bar(page, found_checks)
design_check.tab(page, found_checks)
results_tab.draw(page, found_checks)
