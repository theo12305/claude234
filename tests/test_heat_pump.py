import pytest

from ghe_web import analysis, export, model, plots, properties
from ghe_web.catalog import COOLING_CURVES, HEATING_CURVES


def building_inputs(curve: bool):
    inputs = model.default_inputs()
    inputs["load"].variant = "annual_building"
    inputs["load"].values = properties.get("load").variant("annual_building").defaults()
    if curve:
        inputs["heat_pump"].variant = "curve"
        inputs["heat_pump"].values = properties.get("heat_pump").variant("curve").defaults()
    return inputs


@pytest.fixture(scope="module")
def curve_result():
    inputs = building_inputs(curve=True)
    return inputs, model.size(inputs)


def test_curve_changes_the_design(curve_result):
    _, curved = curve_result
    fixed = model.size(building_inputs(curve=False))
    assert curved.borehole_length != pytest.approx(fixed.borehole_length, rel=0.01)
    # fixed SCOP: the same performance every year
    assert fixed.heat_pump["SPF heating"].nunique() == 1


def test_spf_falls_as_the_ground_cools(curve_result):
    _, result = curve_result
    spf = result.heat_pump["SPF heating"]
    assert spf.iloc[-1] < spf.iloc[0]
    assert 3 < spf.mean() < 7


def test_heat_pump_key_results_and_export(curve_result):
    inputs, result = curve_result
    key = analysis.key_results(result, inputs)
    assert "Heat pump" in key.by_group()
    assert key.values["electricity_mwh"] > 0 and "cop_coldest" in key.values
    for chart in plots.efficiency_curves(inputs["heat_pump"].values, (key.values["t_min"], key.values["t_max"])):
        chart.to_json()
    for chart in plots.heat_pump_yearly_chart(result.heat_pump, show_spf=True):
        chart.to_json()
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(export.excel_workbook(result, inputs)), read_only=True)
    assert "Heat pump" in wb.sheetnames


def test_ground_load_has_no_heat_pump():
    inputs = model.default_inputs()
    inputs["heat_pump"].variant = "curve"
    inputs["heat_pump"].values = properties.get("heat_pump").variant("curve").defaults()
    assert "heat_pump" in model.cross_warnings(inputs)
    assert model.size(inputs).heat_pump is None


def test_presets_match_the_curve_points():
    for curve in list(HEATING_CURVES.values()) + list(COOLING_CURVES.values()):
        assert len(curve) == 5


def test_round_trip_keeps_the_curve():
    inputs = building_inputs(curve=True)
    inputs["heat_pump"].values["cop_0"] = 4.1
    _, loaded = model.from_json(model.to_json(inputs))
    assert loaded["heat_pump"].variant == "curve" and loaded["heat_pump"].values["cop_0"] == 4.1
