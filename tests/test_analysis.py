import pytest

from ghe_web import analysis, model, properties, report
from ghe_web.catalog import GROUND


@pytest.fixture(scope="module")
def sized():
    inputs = model.default_inputs()
    return inputs, model.size(inputs)


def test_presets_only_set_existing_properties():
    for section in properties.sections():
        for variant in section.variants:
            keys = {p.key for p in variant.properties}
            for group in variant.presets:
                for option, values in group.options.items():
                    assert set(values) <= keys, (section.key, variant.key, group.label, option)


def test_rock_preset_gives_valid_inputs():
    inputs = model.default_inputs()
    inputs["ground"].values.update(GROUND["Granite"])
    assert model.validate(inputs) == {}


def test_unusual_values_warn_but_stay_valid():
    inputs = model.default_inputs()
    inputs["ground"].values["k_s"] = 5.5
    inputs["borefield"].values["B_1"] = 3.0
    assert model.validate(inputs) == {}
    warns = model.warnings(inputs)
    assert "ground" in warns and "borefield" in warns


def test_key_results(sized):
    inputs, result = sized
    keys = analysis.key_results(result, inputs)
    labels = [row[0] for row in keys.rows]
    assert "Size decided by" in labels
    assert keys.values["t_min"] > inputs["limits"].values["T_min"] - 0.1
    assert keys.values["dp_kpa"] > 0 and keys.values["pump_w"] > 0
    expected_cost = 45 * result.total_length + 1500 * result.number_of_boreholes + 10000
    assert keys.values["cost"] == pytest.approx(expected_cost)


def test_check_mode_keeps_length_and_reports_failure():
    inputs = model.default_inputs()
    inputs["calculation"].variant = "check"
    inputs["borefield"].values["H"] = 20.0
    result = model.size(inputs)
    assert result.sizing_method == "check"
    assert result.borehole_length == pytest.approx(20.0)
    keys = analysis.key_results(result, inputs)
    assert ("Check against the limits", "fails") == keys.rows[2][:2]


def test_annual_building_load_is_close_to_monthly():
    monthly = model.default_inputs()
    annual = model.default_inputs()
    annual["load"].variant = "annual_building"
    annual["load"].values = properties.get("load").variant("annual_building").defaults()
    a, m = model.size(annual).borehole_length, model.size(monthly).borehole_length
    assert a == pytest.approx(m, rel=0.15)


@pytest.mark.parametrize("variant", ["coaxial", "constant_rb", "double_u"])
def test_pipe_variants_size(variant):
    inputs = model.default_inputs()
    inputs["pipe"].variant = variant
    inputs["pipe"].values = properties.get("pipe").variant(variant).defaults()
    assert 20 < model.size(inputs).borehole_length < 500


def test_round_trip_with_new_sections():
    inputs = model.default_inputs()
    inputs["calculation"].variant = "check"
    inputs["costs"].values["drilling_per_m"] = 60.0
    inputs["ground"].variant = "gradient"
    inputs["ground"].values = properties.get("ground").variant("gradient").defaults()
    _, loaded = model.from_json(model.to_json(inputs))
    assert loaded["calculation"].variant == "check"
    assert loaded["costs"].values["drilling_per_m"] == 60.0
    assert loaded["ground"].variant == "gradient"
    assert model.validate(loaded) == {}


def test_yearly_and_energy_tables(sized):
    inputs, result = sized
    years = inputs["load"].values["simulation_period"]
    assert len(analysis.yearly_extremes(result)) == years
    assert len(analysis.monthly_ground_energy(result)) == 12
    assert len(analysis.gfunction_curve(result)) > 5


def test_sensitivity(sized):
    inputs, result = sized
    table = analysis.sensitivity(inputs)
    assert table["Base"].iloc[0] == pytest.approx(result.borehole_length, rel=0.01)
    conductivity = table[table["Input"].str.startswith("Ground conductivity")].iloc[0]
    assert conductivity["High"] < conductivity["Base"] < conductivity["Low"]


def test_pdf_report(sized):
    inputs, result = sized
    pdf = report.make_pdf(result, inputs, "Test")
    assert pdf.startswith(b"%PDF") and len(pdf) > 10_000
