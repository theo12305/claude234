import pytest

from ghe_web import analysis, export, model, plots, report
from ghe_web.strata import predict, rocks, sources
from ghe_web.strata.predict import Borehole, LogLayer

BML = b"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs" xmlns:gml="http://www.opengis.net/gml"
    xmlns:bml="http://www.infogeo.de/boreholeml/3.0">
  <gml:featureMember>
    <bml:Borehole gml:id="DABO_1">
      <bml:shortName>BK 1</bml:shortName>
      <bml:location><gml:Point srsName="urn:ogc:def:crs:EPSG::5555"><gml:pos>357000 5644000 38.0</gml:pos>
      </gml:Point></bml:location>
      <bml:intervalSeries><bml:IntervalSeries>
        <bml:layer><bml:Interval><bml:from uom="m">0</bml:from><bml:to uom="m">0.4</bml:to>
          <bml:rockCode>Mu</bml:rockCode></bml:Interval></bml:layer>
        <bml:layer><bml:Interval><bml:from uom="m">0.4</bml:from><bml:to uom="m">6.5</bml:to>
          <bml:rockCode>S,G,2</bml:rockCode>
          <bml:lithology><bml:Lithology><bml:rockName>S</bml:rockName></bml:Lithology></bml:lithology>
        </bml:Interval></bml:layer>
        <bml:layer><bml:Interval><bml:from uom="m">6.5</bml:from><bml:to uom="m">30</bml:to>
          <bml:rockCode>XYZ</bml:rockCode>
          <bml:lithology><bml:Lithology><bml:rockName>Tst</bml:rockName></bml:Lithology></bml:lithology>
        </bml:Interval></bml:layer>
      </bml:IntervalSeries></bml:intervalSeries>
    </bml:Borehole>
  </gml:featureMember>
  <gml:featureMember><bml:Borehole gml:id="DABO_2"><bml:shortName>no layers</bml:shortName>
    <bml:location><gml:Point><gml:pos>357100 5644100</gml:pos></gml:Point></bml:location></bml:Borehole>
  </gml:featureMember>
</wfs:FeatureCollection>"""


@pytest.mark.parametrize("text, rock", [
    ("mS,g", "Sand"), ("U,AY,3", "Silt / loess"), ("Tst", "Claystone / siltstone"), ("Ton, sandig", "Clay"),
    ("Sandstein", "Sandstone"), ("Geschiebemergel", "Till / boulder clay"), ("migmatite", "Migmatite"),
    ("mud size sediment", "Silt / loess"), ("Kalkstein, tonig", "Limestone"), ("Grwk", "Greywacke"),
    ("", rocks.UNKNOWN), ("xyz", rocks.UNKNOWN),
])
def test_classify(text, rock):
    assert rocks.classify(text) == rock


def test_loose_sediment_is_worse_above_groundwater():
    assert rocks.values("Sand", saturated=False)[0] < rocks.values("Sand")[0]
    assert rocks.values("Granite", saturated=False) == rocks.values("Granite")


def _hole(name, x, layers, gw=None):
    return Borehole(name, x, 0.0, [LogLayer(t, b, r) for t, b, r in layers], "test", gw)


def test_prediction_follows_the_nearest_logs():
    near = _hole("near", 50, [(0, 10, "Sand"), (10, 40, "Claystone / siltstone")])
    near2 = _hole("near2", -60, [(0, 12, "Sand"), (12, 50, "Claystone / siltstone")], gw=3.0)
    far = _hole("far", 900, [(0, 60, "Granite")])
    result = predict.predict([far, near, near2], 0, 0, depth=80, radius=1000)
    rocks_found = [l.rock for l in result.layers]
    assert rocks_found[0] == "Sand" and "Claystone / siltstone" in rocks_found
    # the sand is split at the groundwater table from the log: moist above, saturated below
    assert result.layers[0].bottom == pytest.approx(3.0) and result.layers[0].k_s < result.layers[1].k_s
    assert result.layers[-1].bottom == 80
    assert sum(w for _, _, w in result.used) == pytest.approx(1.0)
    rows = result.rows()
    assert predict.check_rows(rows) == []
    assert any("deepest log" in n for n in result.notes)


def test_no_logs_uses_the_map():
    result = predict.predict([], 0, 0, depth=100, surface_rock="Granite")
    assert [l.rock for l in result.layers] == ["Granite"]
    assert result.layers[0].confidence < 0.5


def test_thin_layers_are_merged():
    hole = _hole("a", 0, [(0, 20, "Sand"), (20, 20.5, "Peat"), (20.5, 50, "Sand")])
    result = predict.predict([hole], 0, 0, depth=50, min_thickness=1.0)
    assert [l.rock for l in result.layers] == ["Sand"]


def test_effective_matches_ghetool_and_rows_check():
    rows = [{"top": 0, "bottom": 20, "rock": "Sand", "k_s": 1.0, "C": 1.7},
            {"top": 20, "bottom": 60, "rock": "Clay", "k_s": 1.7, "C": 2.4},
            {"top": 60, "bottom": 200, "rock": "Granite", "k_s": 3.4, "C": 2.4}]
    inputs = model.default_inputs()
    inputs["ground"].values["layers"] = {"use": True, "rows": tuple(rows)}
    bf = model.build_borefield(inputs)
    assert predict.effective(rows, 150, 0.7)[0] == pytest.approx(bf.ground_data.k_s(150.7, 0.7))
    assert predict.check_rows(rows[1:])  # does not start at 0
    assert predict.check_rows([{**rows[0], "bottom": 10}, rows[1]])  # gap


def test_layered_sizing_and_project_file():
    inputs = model.default_inputs()
    uniform = model.size(inputs).borehole_length
    poor = [{"top": 0, "bottom": 40, "rock": "Sand", "k_s": 1.0, "C": 1.7},
            {"top": 40, "bottom": 300, "rock": "Clay", "k_s": 1.7, "C": 2.4}]
    inputs["ground"].values["layers"] = {"use": True, "rows": tuple(poor)}
    result = model.size(inputs)
    assert result.borehole_length > uniform  # worse ground than the default 3 W/(m·K)
    name, loaded = model.from_json(model.to_json(inputs, "x"))
    assert loaded["ground"].values["layers"]["use"] is True
    assert loaded["ground"].values["layers"]["rows"][1]["rock"] == "Clay"
    length, k = analysis.uniform_ground_length(result, inputs)
    assert k == pytest.approx(predict.effective(poor, result.borehole_length, 0.7)[0])
    assert length == pytest.approx(result.borehole_length, rel=0.1)
    # exports and the report include the layers
    assert "Input ground layers" in export._table_inputs(inputs)
    assert report.make_pdf(result, inputs, "x")[:4] == b"%PDF"
    plots.ground_log_drawing(inputs)


def test_layers_switched_on_without_rows_is_an_error():
    inputs = model.default_inputs()
    inputs["ground"].values["layers"] = {"use": True, "rows": ()}
    assert "ground" in model.validate(inputs)


def test_parse_bml():
    holes = sources.parse_bml(BML)
    assert len(holes) == 1
    hole = holes[0]
    assert hole.name == "BK 1" and (hole.x, hole.y) == (357000.0, 5644000.0)
    assert [l.rock for l in hole.layers] == ["Topsoil / humus", "Sand", "Claystone / siltstone"]


def test_read_table_template_and_coordinates():
    holes, notes = sources.read_table("t.csv", sources.template_csv())
    assert [h.name for h in holes] == ["BH 1", "BH 2"]
    assert holes[0].x == pytest.approx(350120.0) and holes[0].groundwater == 3.5
    assert [l.rock for l in holes[0].layers] == ["Topsoil / humus", "Sand", "Gravel", "Claystone / siltstone"]
    x, y = sources.to_utm32(2_560_000, 5_640_000)  # Gauß-Krüger zone 2
    assert 300_000 < x < 400_000 and 5_630_000 < y < 5_650_000


def test_table_without_coordinates_goes_on_the_site():
    content = "von;bis;Beschreibung\n0;5;Kies\n5;40;Mergel\n".encode()
    holes, notes = sources.read_table("log.csv", content, site=(1.0, 2.0))
    assert (holes[0].x, holes[0].y) == (1.0, 2.0) and holes[0].layers[1].rock == "Marl"
    with pytest.raises(sources.TableError):
        sources.read_table("log.csv", content)
