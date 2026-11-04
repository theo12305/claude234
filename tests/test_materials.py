"""Material list and horizontal piping: routing, quantities, saving with the project, and the result view registry."""
import math

import pytest

from ghe_web import model, results
from ghe_web.materials import network, quantities as q
from ghe_web.results import registry


@pytest.fixture(scope="module")
def sized():
    inputs = model.default_inputs()
    inputs["borefield"].values.update(N_1=3, N_2=4, H=100.0)
    inputs["calculation"] = type(inputs["calculation"])("check", {**inputs["calculation"].values})
    return model.size(inputs), inputs


def test_auto_routing_is_a_tree_through_all_boreholes():
    bhes = [(x * 6.0, y * 6.0) for x in range(3) for y in range(2)]
    r = network.auto_routing(bhes, (-2.0, 0.0), (-10.0, 0.0))
    assert len(r.trenches) == len(bhes)  # n + 1 nodes, n edges
    assert r.paths[0] == pytest.approx(2.0)  # the BHE at the origin is next to the manifold
    assert max(r.paths) == pytest.approx(2.0 + 12.0 + 6.0)
    assert r.header_length == pytest.approx(8.0)
    assert r.trench_length == pytest.approx(2.0 + 5 * 6.0 + 8.0)


def test_drawn_routing_follows_the_lines_and_joins_crossings():
    bhes = [(0.0, 2.0), (10.0, 2.0)]
    lines = [[(-5.0, 0.0), (15.0, 0.0)], [(5.0, -5.0), (5.0, 5.0)]]  # a cross
    r = network.drawn_routing(bhes, (5.0, -6.0), (5.0, 8.0), lines)
    # BHE (0, 2): stub 2 m to (0, 0), 5 m to the crossing, 5 m down, 1 m stub to the manifold
    assert r.paths[0] == pytest.approx(2 + 5 + 5 + 1)
    assert r.paths[1] == pytest.approx(r.paths[0])
    assert r.header_length == pytest.approx(1 + 5 + 5 + 3)
    assert not r.unconnected
    shared = [c for a, b, c in r.trenches if c == 2]
    assert shared  # both circuits share the trench from the crossing to the manifold


def test_drawn_routing_reports_boreholes_it_cannot_reach():
    bhes = [(0.0, 1.0), (50.0, 50.0)]
    lines = [[(-5.0, 0.0), (5.0, 0.0)], [(45.0, 55.0), (55.0, 55.0)]]  # two separate trenches
    r = network.drawn_routing(bhes, (0.0, -1.0), None, lines)
    assert r.unconnected == [1]
    assert r.paths[1] == pytest.approx(math.dist((50, 50), (0, -1)))


def test_snap_joins_a_click_to_a_nearby_corner():
    assert network.snap((10.3, 0.2), [[(0.0, 0.0), (10.0, 0.0)]], [], 1.0) == (10.0, 0.0)
    assert network.snap((12.0, 0.0), [[(0.0, 0.0), (10.0, 0.0)]], [], 1.0) == (12.0, 0.0)


def test_pipe_size_from_the_velocity():
    d, v = q.pick_pipe(0.6 / 1030, 1.2, "auto")
    assert d == 32 and v <= 1.2
    d, v = q.pick_pipe(12 * 0.6 / 1030, 1.2, "auto")
    assert d == 110 and v <= 1.2
    assert q.pick_pipe(0.001, 1.2, 63)[0] == 63


def test_material_list_quantities(sized):
    result, inputs = sized
    s = q.settings({"entrance": [-10.0, 9.0]})
    items = {it.description: it for it in q.material_list(result, inputs, s)}
    n, H, D = result.number_of_boreholes, result.borehole_length, inputs["borefield"].values["D"]
    assert n == 12
    assert items["Drilled length"].quantity == pytest.approx(n * (H + D))
    probe = next(it for d, it in items.items() if d.startswith("Double U-tube BHE"))
    assert probe.quantity == n and "105 m" in probe.description  # 100.7 m rounded up to 105 m
    grout = next(it for d, it in items.items() if d.startswith("Grout suspension"))
    annulus = math.pi * (0.076 ** 2 - 4 * 0.016 ** 2) * (H + D)
    assert grout.quantity == pytest.approx(annulus * n * 1.15)
    assert any(d.startswith("Notification under mining law") for d in items)  # 100.7 m > 100 m
    assert any(d.startswith("Antifreeze MPG") for d in items)
    assert any(d.startswith("Manifold with 12 circuits") for d in items)


def test_manifold_in_the_building_has_no_header(sized):
    result, inputs = sized
    s = q.settings({"entrance": [-10.0, 9.0], "manifold_mode": "building"})
    items = q.material_list(result, inputs, s)
    assert not any(it.description.startswith("Header pipe") for it in items)
    walls = next(it for it in items if it.description.startswith("Wall penetrations"))
    assert walls.quantity == 2 * result.number_of_boreholes


def test_view_settings_are_saved_with_the_project_but_do_not_change_the_inputs():
    inputs = model.default_inputs()
    plain = model.to_json(inputs)
    saved = model.to_json(inputs, plugins={"materials": {"entrance": (1.0, 2.0), "trenches": []}})
    assert model.saved_plugins(saved) == {"materials": {"entrance": [1.0, 2.0], "trenches": []}}
    assert model.saved_plugins(plain) == {}
    assert model.from_json(saved)[1] == model.from_json(plain)[1]


def test_every_result_view_is_registered_once_in_order():
    keys = [v.key for v in registry.all_views()]
    assert keys[:2] == ["overview", "checks"] and keys[-2:] == ["analysis", "export"]
    assert "materials" in keys and len(keys) == len(set(keys))
    with pytest.raises(ValueError):
        registry.register(registry.get("overview"))
