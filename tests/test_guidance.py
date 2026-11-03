"""Typical ranges, side notes and Simple-mode fields next to the inputs."""
from ghe_web import catalog, guidance, model, properties


def test_rock_ranges_contain_the_dropdown_value():
    # the "Rock type" drop-down fills in a value inside the range shown for that rock
    assert set(guidance.ROCK_CONDUCTIVITY) == set(catalog.GROUND)
    for rock, (lo, hi) in guidance.ROCK_CONDUCTIVITY.items():
        assert lo <= catalog.GROUND[rock]["k_s"] <= hi, rock


def test_verdict_and_bar_position():
    rng = guidance.Typical(1.5, 3.5, "usual in Germany")
    assert guidance.verdict(1.0, rng) == "low"
    assert guidance.verdict(2.0, rng) == "typical"
    assert guidance.verdict(4.0, rng) == "high"
    lo, hi, band_lo, band_hi = guidance.position(2.0, rng, 0.1, 10.0)
    assert lo < 1.5 < 3.5 < hi and 0 < band_lo < band_hi < 1
    # a value far outside still lands on the bar
    lo, hi, _, _ = guidance.position(9.0, rng, 0.1, 10.0)
    assert hi >= 9.0


def test_side_notes():
    assert "m³/h" in guidance.side_note("mfr", 0.3, {})
    assert guidance.side_note("H", 90.0, {"D": 0.7}) is None
    assert "BBergG" in guidance.side_note("H", 100.0, {"D": 0.7})
    hours = guidance.side_note("annual_heating_mwh", 400.0, {"peak_heating_kw": 200.0})
    assert "2,000" in hours


def test_advanced_fields_exist():
    keys = {(s.key, p.key) for s in properties.sections() for v in s.variants for p in v.properties}
    assert guidance.ADVANCED <= keys


def test_mode_is_saved_with_the_project():
    text = model.to_json(model.default_inputs(), "x", language="de", mode="expert")
    assert model.saved_setting(text, "mode") == "expert"
    assert model.saved_language(text) == "de"
    assert model.from_json(text)[0] == "x"
