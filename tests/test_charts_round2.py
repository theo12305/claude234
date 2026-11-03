"""Result charts for clients: plain labels, the ground map classes and the picture download."""
import json

import numpy as np
import pytest

from ghe_web import analysis, i18n, model, plots


@pytest.fixture(scope="module")
def result():
    return model.size(model.default_inputs())


def test_when_names_year_and_month():
    with i18n.using("en"):
        assert plots.when(1 / 12) == "year 1, January"
        assert plots.when(8 / 12) == "year 1, August"
        assert plots.when(589 / 12) == "year 50, January"
        assert plots.when(50.0) == "year 50, December"
    with i18n.using("de"):
        assert plots.when(14 / 12) == "Jahr 2, Februar"


def test_ground_classes_are_round_steps():
    step, levels = plots.ground_classes(np.array([-8.4, -0.1]))
    assert step == 1.0
    assert levels == [-8.0, -7.0, -6.0, -5.0, -4.0, -3.0, -2.0, -1.0]
    step, levels = plots.ground_classes(np.array([-0.3, 0.45]))
    assert step == 0.1 and 0.0 not in levels


def test_result_charts_build(result):
    limits = {"T_min": 0.0, "T_max": 17.0}
    energy = analysis.monthly_ground_energy(result)
    m = analysis.ground_temperature_map(result)
    for c in (plots.temperature_chart(result.temperatures, limits),
              plots.temperature_chart(result.temperatures, limits, (10, 20)),
              plots.last_year_chart(result.temperatures, limits, compact=True),
              plots.energy_balance_chart(energy), plots.imbalance_chart(energy, 50),
              plots.ground_map_chart(m, north=True), plots.ground_map_chart(m, size=290),
              plots.ground_profile_chart(m)):
        c.to_dict()


def test_energy_colours_follow_the_ground(result):
    spec = plots.energy_balance_chart(analysis.monthly_ground_energy(result)).to_dict()
    scale = spec["layer"][0]["encoding"]["color"]["scale"]
    assert scale["range"][:2] == [plots.EXTRACTION, plots.INJECTION]
    assert plots.EXTRACTION == plots.SERIES_COLORS["Average fluid (peak extraction)"]  # blue, like the cold fluid


def test_picture_download(result):
    vlc = pytest.importorskip("vl_convert")
    spec = plots.imbalance_chart(analysis.monthly_ground_energy(result), 50).to_dict()
    spec["config"] = i18n.chart_config(background="white").to_dict()
    assert vlc.vegalite_to_png(spec, scale=1)[:4] == b"\x89PNG"
    assert vlc.vegalite_to_svg(spec).startswith("<svg")


def test_address_is_saved_with_the_project():
    text = model.to_json(model.default_inputs(), "x", address="Lindenstraße 12, Freiburg")
    assert json.loads(text)["address"] == "Lindenstraße 12, Freiburg"
    assert model.saved_setting(text, "address") == "Lindenstraße 12, Freiburg"
    assert "address" not in json.loads(model.to_json(model.default_inputs(), "x"))
    model.from_json(text)  # still opens
