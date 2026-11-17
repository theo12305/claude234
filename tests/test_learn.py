"""Learn mode (ghe_web/learn): the source numbers hold together, the explanations add up to the real result, and the
three Learn tabs open in Streamlit's test runner."""
import pathlib

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from ghe_web import i18n
from ghe_web.core import analysis, model
from ghe_web.inputs import registry as input_registry
from ghe_web.learn import exercises, explain, glossary, modules, sources

APP = str(pathlib.Path(__file__).resolve().parents[1] / "app.py")


def test_source_numbers_are_stable_and_every_reference_exists():
    numbers = [s.number for s in sources.SOURCES]
    assert numbers == list(range(1, len(numbers) + 1))
    used = {n for m in modules.MODULES for n in m.sources} | {n for term in glossary.TERMS for n in term.sources}
    assert used <= set(numbers)
    assert all(s.url.startswith("https://") for s in sources.SOURCES)
    assert len({s.key for s in sources.SOURCES}) == len(numbers)
    assert sources.bibtex().count("@") == len(numbers)


def test_modules_and_glossary_link_up():
    assert [m.number for m in modules.MODULES] == list(range(8))
    keys = {term.key for term in glossary.TERMS}
    assert {k for m in modules.MODULES for k in m.terms} <= keys
    assert {term.module for term in glossary.TERMS} <= {m.number for m in modules.MODULES}
    from ghe_web.learn.page import EXERCISES
    assert {e for m in modules.MODULES for e in m.exercises} <= set(EXERCISES)
    fields = {p.key for s in input_registry.sections() for v in s.variants for p in v.properties}
    assert set(glossary.FIELDS) <= fields
    for m in modules.MODULES:  # both languages filled in
        assert m.body_en.strip() and m.body_de.strip() and m.title_en and m.title_de


def test_coldest_month_breakdown_adds_up_to_the_fluid_temperature():
    inputs = exercises.practice_inputs()
    result = model.size(inputs)
    b = analysis.coldest_breakdown(result)
    assert b is not None
    tg = b["t_ground"]
    assert tg + sum(v for _, v in b["parts"]) == pytest.approx(b["fluid"], abs=1e-6)
    assert b["fluid"] == pytest.approx(b["limit"], abs=0.1)  # sized to the limit
    steps = explain.why(result, analysis.key_results(result, inputs))
    assert len(steps) == 4
    parts = explain.resistance_parts(result, b["fluid"])
    assert sum(r for _, r in parts) == pytest.approx(result.borehole_resistance, rel=1e-6)


def test_sweep_gives_shorter_boreholes_for_better_ground():
    df = analysis.sweep(exercises.practice_inputs(), "ground", "k_s", [1.5, 2.0, 3.0])
    assert list(df.columns) == ["Value", "Length"]
    assert np.all(np.diff(df["Length"]) < 0)


def test_explanations_in_german():
    with i18n.using("de"):
        assert modules.MODULES[1].title == modules.MODULES[1].title_de
        assert "Planungsrichtlinie" in sources.get(4).why


@pytest.mark.slow
def test_learn_tabs_open():
    at = AppTest.from_file(APP, default_timeout=600)
    at.run()
    next(b for b in at.button if "Borehole" in b.label).click()
    at.run()
    at.session_state["ui_mode"] = "learn"
    at.run()
    assert not at.exception, at.exception
    for tab in (":material/school: Introduction", ":material/dictionary: Glossary", ":material/menu_book: Literature"):
        at.session_state["step"] = tab
        at.run()
        assert not at.exception, (tab, [e.value for e in at.exception])
    at.session_state["step"] = ":material/school: Introduction"
    for number in range(len(modules.MODULES)):
        at.session_state["learn_module"] = number
        at.run()
        assert not at.exception, (number, [e.value for e in at.exception])
    at.session_state["calc_requested"] = True
    at.run()
    assert not at.exception, [e.value for e in at.exception]
