"""Outputs added after comparing with GHEtool Cloud, and the fixes from the maths and physics review."""
import numpy as np
import pygfunction as gt
import pytest

from ghe_web import analysis, model, properties, report
from ghe_web.catalog import FLUIDS


def _hourly_inputs(years=10, **overrides):
    inputs = model.default_inputs()
    inputs["load"].variant = "hourly_building"
    inputs["load"].values = properties.get("load").variant("hourly_building").defaults()
    inputs["load"].values.update(simulation_period=years, **overrides)
    return inputs


@pytest.fixture(scope="module")
def sized():
    inputs = model.default_inputs()
    return inputs, model.size(inputs)


@pytest.fixture(scope="module")
def hourly_check():
    """A field that is too short for the hourly demand, so the optimisation has to split the load."""
    inputs = _hourly_inputs()
    inputs["calculation"].variant = "check"
    inputs["borefield"].values["H"] = 40.0
    return inputs, model.size(inputs)


def test_default_period_is_50_years():
    assert model.default_inputs()["load"].values["simulation_period"] == 50


def test_costs_are_gone(sized):
    inputs, result = sized
    assert "costs" not in inputs
    assert "Cost" not in analysis.key_results(result, inputs).by_group()


@pytest.mark.parametrize("variant, change, message", [
    ("single_u", {"D_s_mm": 65.0}, "stick out"),
    ("double_u", {"D_s_mm": 20.0, "r_out_mm": 20.0, "r_in_mm": 16.0}, "overlap"),
    ("coaxial", {"r_out_out_mm": 80.0}, "does not fit"),
])
def test_pipes_must_fit_in_the_borehole(variant, change, message):
    inputs = model.default_inputs()
    inputs["pipe"].variant = variant
    inputs["pipe"].values = properties.get("pipe").variant(variant).defaults() | change
    errors = model.validate(inputs)
    assert message in " ".join(errors.get("pipe", []))


def test_pipe_presets_fit_the_default_borehole():
    section = properties.get("pipe")
    for variant in ("single_u", "double_u", "coaxial"):
        inputs = model.default_inputs()
        inputs["pipe"].variant = variant
        inputs["pipe"].values = section.variant(variant).defaults()
        assert model.validate(inputs) == {}, variant


def test_fluid_ranges_are_accepted_by_ghetool():
    from GHEtool import TemperatureDependentFluidData
    for name, (low, high) in FLUIDS.items():
        if name == "Water":
            continue
        for share in (low, high):
            TemperatureDependentFluidData(name, share).rho(temperature=0.0)


@pytest.mark.parametrize("hour, month", [(0, "Jan"), (740, "Jan"), (744, "Feb"), (1420, "Mar"), (8020, "Dec")])
def test_month_of_an_hour(hour, month):
    assert analysis._when(hour, 8760).startswith(month)


def test_hourly_sizing_reports_hourly_values():
    result = model.size(_hourly_inputs(years=5, hourly_sizing=True))
    assert result.hourly_basis and result.reynolds > 0
    key = analysis.key_results(result, _hourly_inputs(years=5, hourly_sizing=True))
    hourly = result.hourly_temperatures
    assert key.values["t_min"] == pytest.approx(hourly["Average fluid"].min())
    assert key.values["t_inlet_min"] == pytest.approx(hourly["Into borefield"].min())
    assert key.values["t_min"] > -0.1  # the limit, checked hour by hour
    assert len(analysis.yearly_extremes(result)) == 5


def test_pump_energy(sized):
    inputs, result = sized
    hyd = analysis.hydraulics(result, inputs)
    flow = inputs["flow"].values
    assert hyd["pump_electric_w"] == pytest.approx(hyd["pump_w"] / (flow["pump_efficiency"] / 100))
    assert hyd["pump_mwh"] == pytest.approx(hyd["pump_electric_w"] * flow["pump_hours"] / 1e6)


def test_pressure_drop_curve_rises(sized):
    _, result = sized
    curve = analysis.pressure_drop_curve(result, 0.0)
    assert np.all(np.diff(curve["Pressure drop [kPa]"]) > 0)


def test_load_optimisation_splits_the_demand(hourly_check):
    _, result = hourly_check
    opt = analysis.load_optimisation(result, "power")
    assert 0 < opt["heating_share"] < 1
    assert opt["backup_heating_kw"] > 0
    building = opt["first_year"]["Building heating [kW]"]
    parts = opt["first_year"]["Ground heating [kW]"] + opt["first_year"]["External heating [kW]"]
    assert np.allclose(building, parts, atol=1e-6)
    monthly = opt["monthly"]
    assert monthly["Ground heating [MWh]"].sum() == pytest.approx(
        opt["heating_share"] * monthly["Building heating [MWh]"].sum())


def test_load_optimisation_needs_hourly_demand(sized):
    assert analysis.load_optimisation(sized[1]) is None


def test_load_duration(hourly_check):
    df = analysis.load_duration(hourly_check[1])
    assert len(df) == 8760
    assert (df["Heating demand"].diff().dropna() <= 0).all()
    assert "Ground extraction" in df


def test_ground_map_matches_pygfunction():
    """The line source used for the map gives the same borehole wall temperature as pygfunction."""
    from scipy.special import erfc
    H, D, r_b, k, alpha = 100.0, 4.0, 0.075, 3.0, 3.0 / 2.4e6
    t = 50 * 8760 * 3600.0
    g = gt.gfunction.gFunction([gt.boreholes.Borehole(H, D, r_b, 0, 0)], alpha, time=np.array([t]),
                               boundary_condition="UHTR").gFunc[0]
    zs, zp = np.linspace(D, D + H, 4001), np.linspace(D, D + H, 201)
    d1 = np.sqrt(r_b ** 2 + (zp[:, None] - zs) ** 2)
    d2 = np.sqrt(r_b ** 2 + (zp[:, None] + zs) ** 2)
    s = 2 * np.sqrt(alpha * t)
    mean = np.trapezoid(erfc(d1 / s) / d1 - erfc(d2 / s) / d2, zs, axis=1).mean() / (4 * np.pi * k)
    assert mean == pytest.approx(g / (2 * np.pi * k), rel=0.01)


def test_ground_map_cools_with_net_extraction(sized):
    _, result = sized
    m = analysis.ground_temperature_map(result, cells=40)
    assert m["q_w_per_m"] < 0  # the default load takes more heat out than it puts in
    assert m["table"]["Change"].max() < 0
    assert m["years"] == 50


def test_reports(hourly_check):
    inputs, result = hourly_check
    extras = {"ground_map": analysis.ground_temperature_map(result, cells=40),
              "load_optimisation": analysis.load_optimisation(result, "power")}
    options = report.ReportOptions(title="Test", subtitle="Sub", author="A", company="C", client="Client",
                                   introduction="Intro.\nSecond paragraph.", conclusion="Done.")
    full = report.make_pdf(result, inputs, "x", options, extras)
    summary = report.make_pdf(result, inputs, "x", report.ReportOptions(kind="summary"))
    assert full.startswith(b"%PDF") and summary.startswith(b"%PDF")
    def pages(pdf):
        return pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages")

    assert pages(summary) == 1
    assert pages(full) > 6
