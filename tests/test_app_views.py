"""The whole page in Streamlit's test runner: size the default borefield and show every section of the results sheet,
in both modes without an exception (German texts: test_i18n.py). Guards the result view plug-ins
(ghe_web/results) and the results sheet switches (ghe_web/results/sheet.py)."""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


def _sized(mode, language):
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["language"] = language
    at.run()
    next(b for b in at.button if "Borehole" in b.label or "Erdwärmesonden" in b.label).click()
    at.run()
    at.session_state["ui_mode"] = mode
    at.run()
    at.session_state["calc_requested"] = True
    at.run()
    assert not at.exception, at.exception
    assert "result_json" in at.session_state
    return at


@pytest.mark.parametrize("mode,language", [("expert", "en"), ("simple", "en")])
def test_every_section_of_the_results_sheet_opens(mode, language):
    from ghe_web.results import sheet
    at = _sized(mode, language)
    # everything on, then everything off
    every = {f"section.{k}": True for k in sheet.SECTION_DEFAULTS}
    every |= {p: True for parts in sheet.PARTS.values() for p, _, _ in parts}
    for value in (True, False):
        store = {k: value for k in every}
        store["style"] = {name: value for name in sheet.STYLE_LABELS}
        at.session_state["plugin_data"] = {sheet.KEY: store}
        at.run()
        assert not at.exception, (value, [e.value for e in at.exception])
    # the design check step and its confirm button
    assert any(b.key == "check_confirm" for b in at.button)


def test_hidden_views_stay_registered_but_are_not_shown():
    from ghe_web.results import registry
    keys = [v.key for v in registry.all_views()]
    for key in ("overview", "checks", "heat_pump", "hydraulics", "materials"):
        assert key in keys and registry.get(key).available(None) is False
    assert not registry.get("analysis").on_sheet and not registry.get("export").on_sheet
