"""The whole page in Streamlit's test runner: size the default borefield and open every result view, in both modes
without an exception (German texts: test_i18n.py). Guards the result view plug-ins (ghe_web/results)."""
import pathlib

import pytest
from streamlit.testing.v1 import AppTest

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


@pytest.mark.parametrize("mode,language", [("expert", "en"), ("simple", "en")])
def test_every_result_view_opens(mode, language):
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
    from ghe_web import i18n
    from ghe_web.results import registry
    at.session_state["all_views"] = True
    at.run()
    shown = at.selectbox(key="result_view_id").options
    with i18n.using(language):
        keys = [v.key for v in registry.all_views() if i18n.t(v.title) in shown]
    assert "materials" in keys and len(keys) >= 10
    for key in keys:
        at.session_state["result_view_id"] = key
        at.session_state["all_views"] = True
        at.run()
        assert not at.exception, (key, [e.value for e in at.exception])
