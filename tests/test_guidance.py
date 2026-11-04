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
    energy = guidance.side_note("full_load_hours_heating", 2000.0, {"peak_heating_kw": 200.0})
    assert "400.0 MWh/yr" in energy


def test_old_projects_with_yearly_energy_become_full_load_hours():
    import json
    text = json.loads(model.to_json(model.default_inputs()))
    values = text["sections"]["load"]["values"] = {"annual_heating_mwh": 300.0, "peak_heating_kw": 150.0,
                                                  "annual_cooling_mwh": 40.0, "peak_cooling_kw": 0.0}
    text["sections"]["load"]["variant"] = "annual_building"
    _, inputs = model.from_json(json.dumps(text))
    assert values and inputs["load"].values["full_load_hours_heating"] == 2000.0
    assert inputs["load"].values["full_load_hours_cooling"] == 0.0


def test_advanced_fields_exist():
    keys = {(s.key, p.key) for s in properties.sections() for v in s.variants for p in v.properties}
    assert guidance.ADVANCED <= keys


def test_mode_is_saved_with_the_project():
    text = model.to_json(model.default_inputs(), "x", language="de", mode="expert")
    assert model.saved_setting(text, "mode") == "expert"
    assert model.saved_language(text) == "de"
    assert model.from_json(text)[0] == "x"


def test_simple_hidden_fields_exist():
    keys = {(s.key, p.key) for s in properties.sections() for v in s.variants for p in v.properties}
    assert guidance.SIMPLE_HIDDEN <= keys


def test_defaults_match_a_drop_down_choice():
    """The drop-downs start on a typical choice, so the default values are one of their options."""
    for section in properties.sections():
        for variant in section.variants:
            defaults = variant.defaults()
            for group in variant.presets:
                assert any(all(abs(float(defaults[k]) - float(v)) < 1e-9 for k, v in vals.items())
                           for vals in group.options.values()), (section.key, variant.key, group.label)


def test_double_u_tube_is_the_default():
    assert properties.get("pipe").variant().key == "double_u"
