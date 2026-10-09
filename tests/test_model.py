from ghe_web import model, properties


def test_every_section_has_valid_defaults():
    assert model.validate(model.default_inputs()) == {}


def test_out_of_range_value_is_reported():
    inputs = model.default_inputs()
    inputs["ground"].values["k_s"] = -1
    assert "ground" in model.validate(inputs)


def test_cross_property_check():
    inputs = model.default_inputs()
    inputs["pipe"].values["r_out_mm"] = inputs["pipe"].values["r_in_mm"] - 1
    assert "pipe" in model.validate(inputs)


def test_every_variant_builds():
    for section in properties.sections():
        for variant in section.variants:
            variant.build(variant.defaults())


def test_sizing_with_defaults():
    result = model.size(model.default_inputs())
    assert 20 < result.borehole_length < 500
    assert result.number_of_boreholes == 120


def test_sizing_returns_monthly_temperatures():
    result = model.size(model.default_inputs())
    years = model.default_inputs()["load"].values["simulation_period"]
    assert len(result.temperatures) == 12 * years
    # sized so the fluid stays within the limits (small tolerance for the sizing iteration)
    assert result.temperatures["Average fluid (peak extraction)"].min() > -0.1
    assert result.temperatures["Average fluid (peak injection)"].max() < 17.1


def test_project_round_trip():
    inputs = model.default_inputs()
    inputs["pipe"].variant = "double_u"
    inputs["ground"].values["k_s"] = 2.2
    name, loaded = model.from_json(model.to_json(inputs, "Office"))
    assert name == "Office"
    assert loaded["pipe"].variant == "double_u"
    assert loaded["ground"].values["k_s"] == 2.2
    assert model.validate(loaded) == {}


def test_old_project_files_stay_loadable():
    # unknown sections/values are ignored, missing ones get defaults
    text = '{"format": 1, "sections": {"ground": {"variant": "constant", "values": {"k_s": 1.8, "old": 3}},' \
           ' "removed_section": {"variant": "x", "values": {}}}}'
    _, loaded = model.from_json(text)
    assert loaded["ground"].values["k_s"] == 1.8
    assert model.validate(loaded) == {}
