"""Learn mode (ghe_web/learn): the example projects size, the stored sensitivities still match the sizing, the
explanations add up to the real result, the source numbers hold together and the Learn page opens in Streamlit's
test runner."""
import pathlib

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from ghe_web import i18n
from ghe_web.core import analysis, model
from ghe_web.learn import explain, glossary, projects, sources

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


def test_source_numbers_are_stable_and_every_reference_exists():
    numbers = [s.number for s in sources.SOURCES]
    assert numbers == list(range(1, len(numbers) + 1))
    assert {n for term in glossary.TERMS for n in term.sources} <= set(numbers)
    assert all(s.url.startswith("https://") for s in sources.SOURCES)
    assert len({s.key for s in sources.SOURCES}) == len(numbers)
    assert sources.bibtex().count("@") == len(numbers)


def test_every_parameter_has_a_term_and_an_input():
    for p in projects.PARAMETERS:
        assert p.term in glossary.BY_KEY
        assert projects.prop(p).key == p.key
        for project in projects.PROJECTS:
            assert np.isfinite(projects.value(project.inputs(), p))
    fields = {q.key for s in __import__("ghe_web.inputs", fromlist=["registry"]).registry.sections()
              for v in s.variants for q in v.properties}
    assert set(glossary.FIELDS) <= fields
    for term in glossary.TERMS:  # both languages filled in
        assert term.text_en.strip() and term.text_de.strip()


def test_stored_lengths_match_the_sizing():
    stored = projects.stored()
    assert set(stored) == {p.key for p in projects.PROJECTS}
    for project in projects.PROJECTS:
        length = model.size(project.inputs()).borehole_length
        assert length == pytest.approx(stored[project.key]["length"], rel=0.01), project.key
        assert set(stored[project.key]["sensitivity"]) == {f"{p.section}.{p.key}" for p in projects.PARAMETERS}


def test_sensitivities_have_the_expected_signs():
    s = projects.stored()["house"]["sensitivity"]
    assert s["ground.k_s"] < 0 and s["pipe.k_g"] < 0  # better conduction: shorter
    assert s["ground.T_g"] < 0 and s["limits.T_min"] > 0  # warmer ground shorter, stricter limit longer
    assert s["load.peak_heating_kw"] > 0
    q = projects.stored()["quarter"]["sensitivity"]
    assert q["borefield.B_1"] < s["borefield.B_1"] <= 0  # spacing matters more in the large field


def test_temperature_budget_adds_up_and_the_why_steps():
    inputs = projects.BY_KEY["office"].inputs()
    result = model.size(inputs)
    b = analysis.coldest_breakdown(result)
    assert b["t_ground"] + sum(v for _, v in b["parts"]) == pytest.approx(b["fluid"], abs=1e-6)
    assert explain.breakdown(result)["rows"][-1]["End"] == pytest.approx(b["fluid"], abs=1e-6)
    steps = explain.why(result, analysis.key_results(result, inputs))
    assert len(steps) == 4
    parts = explain.resistance_parts(result, b["fluid"])
    assert sum(r for _, r in parts) == pytest.approx(result.borehole_resistance, rel=1e-6)


def test_regeneration_shortens_the_drift_dominated_field():
    df = projects.regeneration_study(projects.BY_KEY["quarter"].inputs(), shares=(0.0, 0.5))
    assert df["Length"].iloc[1] < 0.7 * df["Length"].iloc[0]


def test_texts_in_german():
    with i18n.using("de"):
        assert projects.BY_KEY["house"].title == "Einfamilienhaus, nur Heizen"
        assert "Planungsrichtlinie" in sources.get(4).why
        assert glossary.BY_KEY["k_s"].name == "Wärmeleitfähigkeit des Untergrunds"


@pytest.mark.slow
@pytest.mark.parametrize("language", ["en", "de"])
def test_learn_page_opens(language):
    at = AppTest.from_file(APP, default_timeout=900)
    at.session_state["language"] = language
    at.session_state["ui_mode"] = "learn"
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    for project in ("office", "quarter"):
        at.session_state["learn_project"] = project
        at.run()
        assert not at.exception, (project, [e.value for e in at.exception])
    from ghe_web.learn.page import STUDIES
    at.session_state["learn_project"] = "house"
    for study in STUDIES:
        at.session_state["learn_study"] = study
        at.run()
        assert not at.exception, (study, [e.value for e in at.exception])
