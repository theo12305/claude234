"""Groundwater wells (open loop): hydraulics and thermal model against textbook results, and the sizing."""
import math

import numpy as np
import pytest
from scipy.special import exp1

from ghe_web import model
from ghe_web.properties import SectionInput
from ghe_web.wells import aquifer, checks, design, hydraulics as hy, report, thermal as th


def open_inputs(**wells):
    inputs = model.default_inputs()
    inputs["system"] = SectionInput("open", {})
    if wells:
        inputs["wells"] = SectionInput("check", {**model.properties.get("wells").variant("check").defaults(),
                                                 **wells})
    return inputs


def test_doublet_drawdown_is_thiem():
    q, transmissivity, r_w, distance = 0.01, 0.02, 0.2, 30.0
    wells = [hy.Well(0, 0, q), hy.Well(distance, 0, -q)]
    s = hy.head_change(wells, 0, 0, transmissivity, r_w)
    assert s == pytest.approx(q / (2 * math.pi * transmissivity) * math.log(distance / r_w))
    assert hy.head_change(wells, distance, 0, transmissivity, r_w) == pytest.approx(-s)


def test_flows_must_balance():
    with pytest.raises(ValueError):
        hy.head_change([hy.Well(0, 0, 0.01), hy.Well(10, 0, -0.005)], 0, 0, 0.01, 0.2)


def test_unconfined_corrections():
    assert hy.unconfined_drawdown(1.0, 20.0) > 1.0  # a thinner water column draws down more
    assert hy.unconfined_rise(1.0, 20.0) < 1.0
    assert hy.unconfined_drawdown(10.0, 20.0) == math.inf  # runs dry


def test_cooper_jacob_recovers_theis():
    transmissivity, storage, q, r = 5e-3, 2e-4, 0.01, 20.0
    times = np.geomspace(600, 3 * 86400, 30)
    s = q / (4 * math.pi * transmissivity) * exp1(r ** 2 * storage / (4 * transmissivity * times))
    t_fit, s_fit = hy.cooper_jacob_fit(times, s, q, r)
    assert t_fit == pytest.approx(transmissivity, rel=0.05)
    assert s_fit == pytest.approx(storage, rel=0.2)


def test_tracing_matches_the_doublet_breakthrough():
    q, b, n, distance = 0.005, 10.0, 0.2, 20.0
    lines = th.trace([hy.Well(0, 0, q), hy.Well(distance, 0, -q)], b, n, 0.0, 1e12)
    assert lines.first_arrival == pytest.approx(th.doublet_breakthrough(q, b, n, distance), rel=0.03)


def test_no_backflow_beyond_the_critical_distance():
    q, b, n, darcy = 0.005, 10.0, 0.2, 2e-6
    critical = th.critical_distance(q, b, darcy)
    near = th.trace([hy.Well(0, 0, q), hy.Well(0.5 * critical, 0, -q)], b, n, darcy, 1e12)
    far = th.trace([hy.Well(0, 0, q), hy.Well(1.2 * critical, 0, -q)], b, n, darcy, 1e12)
    assert near.captured_fraction > 0
    assert far.captured_fraction == 0


def test_production_temperature_follows_the_returning_water():
    spread = np.full(24, -4.0)
    dev = th.production_temperature(spread, np.array([3.0]), np.array([0.5]))
    assert np.all(dev[:3] == 0)
    assert dev[3] == pytest.approx(-2.0)  # half of the (-4 K) water injected three months earlier


def test_plume_grows_downstream_only():
    xs = np.array([-50.0, 50.0])
    dt = th.plume(-10000, 10, 2.5e6, 2.4, 1e-6, 5, 0.5, 10, xs, np.array([0.0]))[0]
    assert dt[1] < dt[0] < 0  # colder downstream than upstream
    assert th.plume_length(0, 10, 2.5e6, 2.4, 1e-6, 5, 0.5, 10, 1.0) == 0


def test_aquifer_from_layers():
    rows = [{"top": 0, "bottom": 2, "rock": "Topsoil / humus"}, {"top": 2, "bottom": 8, "rock": "Sand"},
            {"top": 8, "bottom": 18, "rock": "Gravel"}, {"top": 18, "bottom": 40, "rock": "Clay"}]
    guess = aquifer.from_layers(rows, groundwater_depth=4.0)
    assert (guess.top, guess.bottom) == (4.0, 18.0)
    assert aquifer.hydraulic("Sand")[0] < guess.kf < aquifer.hydraulic("Gravel")[0]
    assert aquifer.from_layers(rows[-1:], 4.0) is None


def test_open_loop_ignores_borehole_inputs():
    inputs = open_inputs()
    inputs["limits"].values["T_max"] = -5.0  # an error in the closed-loop limits
    assert model.validate(inputs) == {}
    inputs["system"] = SectionInput("closed", {})
    assert "limits" in model.validate(inputs)


def test_sizing_meets_the_limits():
    inputs = open_inputs()
    d = design.size(inputs)
    limits = inputs["well_limits"].values
    assert d.feasible
    assert d.drift <= limits["drift"]
    assert d.peak.drawdown <= d.drawdown_allowed
    assert d.peak.rise <= d.rise_allowed
    assert d.q_peak == pytest.approx(160e3 / (hy.C_W * limits["spread"]))
    assert d.volume_year > 0 and d.pump_energy_year > 0
    assert not [c for c in checks.result_checks(d, inputs) if c.level == checks.PROBLEM]


def test_wells_too_close_are_flagged():
    d = design.size(open_inputs(distance=5.0))
    found = {c.title: c.level for c in checks.result_checks(d, open_inputs(distance=5.0))}
    assert d.breakthrough_years is not None
    assert found["Thermal short circuit"] == checks.PROBLEM


def test_poor_aquifer_needs_more_wells():
    inputs = open_inputs()
    inputs["aquifer"].values["kf"] = 1e-4
    d = design.size(inputs)
    assert d.n_production > 1 or d.n_injection > 1


def test_water_quality_checks():
    inputs = open_inputs()
    inputs["water_quality"] = SectionInput("analysis", {"iron": 1.0, "manganese": 0.3, "oxygen": 5.0, "ph": 7.0,
                                                        "chloride": 40.0, "sulfate": 50.0})
    found = {c.title: c.level for c in checks.water_checks(inputs)}
    assert found["Clogging (ochre)"] == checks.PROBLEM
    assert found["Corrosion and scaling"] == checks.FINE


def test_exports_and_project_round_trip():
    inputs = open_inputs()
    d = design.size(inputs)
    assert report.workbook(d, inputs, "Test")[:2] == b"PK"
    assert report.pdf(d, inputs, "Test")[:4] == b"%PDF"
    _, loaded = model.from_json(model.to_json(inputs))
    assert model.system(loaded) == "open"


def test_site_plan_puts_injection_downstream():
    from shapely.geometry import box
    from ghe_web.siteplan.layout import Rules, Site, allowed_area, place_wells
    parcel = box(0, 0, 60, 30)
    area = allowed_area(Site(parcel), Rules(border_distance=3))
    placed = place_wells(area, parcel, direction=90)  # flow to the east
    (px, _), (ix, _) = placed.production[0], placed.injection[0]
    assert px < 5 and ix > 55
    assert placed.border_downstream == pytest.approx(60 - ix, abs=0.1)
    two = place_wells(area, parcel, direction=270, n_production=2, n_injection=2, spacing=10)
    assert two.production[0][0] > two.injection[0][0]  # flow to the west: injection on the west side
    assert math.dist(*two.production) == pytest.approx(10)
    assert place_wells(area, parcel, 90, n_production=5, spacing=10) is None  # five in a row do not fit across


def test_sources_cover_every_model():
    from ghe_web.wells import sources
    text = sources.markdown()
    for name in ("Thiem", "Sichardt", "Gringarten", "Clyde", "Hähnlein", "Jacob"):
        assert name in text
