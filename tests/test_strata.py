import pytest

from ghe_web import analysis, export, model, plots, report
from ghe_web.siteplan import states
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


# Answers of the state services as they came back when they were checked (2026-10-18), shortened
STATE_ANSWERS = {
    "BB": {"type": "FeatureCollection", "features": [{"type": "Feature", "id": "bpk_m_sch_50419", "geometry": {
        "type": "MultiPoint", "coordinates": [[13.094439129726357, 52.343431736087446]]}, "properties": {
        "Bohrungs_ID": 364400258, "Schichtenverzeichnis_grafisch": "https://geo.brandenburg.de/karten/bpk24/x364400258.png",
        "Bohrungsname": "Hy BghRb 11/67", "HoeheNN_in_m": 33.6, "Ostwert": 370191.7, "Nordwert": 5800946.0,
        "Teufe_in_m": 8.2, "Aufschlussart": "MS", "Schichtenverzeichnis": 1}}]},
    "BE": {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25833"}},
           "features": [{"type": "Feature", "id": "bohrpunkte.413A00103", "geometry": {
               "type": "Point", "coordinates": [391000.0, 5819000.0]}, "properties": {
               "schluessel": "413A00103", "xcoord": 391000.0, "ycoord": 5819000.0, "endteufe": 12,
               "ansatzhoehe": "34.32", "langname": None, "profil": "https://example.invalid/p.jpg",
               "profil_lang": None}}]},
    "SN": {"features": [{"attributes": {"IDENT": 591302, "AKBEZ": "6....1....2016", "RECHTSWERT": 411420.31,
                                        "HOCHWERT": 5656933.11, "ENDTEUFE": 10.0, "HAT_FACHDATEN": 1.0,
                                        "URL": "https://www.umwelt.sachsen.de/umwelt/infosysteme/geodin/getportalpage"},
                         "geometry": {"x": 350000.0, "y": 5660000.0}}]},
    "HE": {"features": [{"attributes": {"ARNUM": 5151, "ANAME": "5151 BK 2/97", "OSTWERT": 476808.365,
                                        "NORDWERT": 5551366.571, "ET": 40, "FORMATION": "AQT", "GW": 12.87},
                         "geometry": {"x": 476808.365, "y": 5551366.571}}]},
    "SH": {"type": "FeatureCollection", "features": [{"type": "Feature", "id": "ID_LONGNAME.2323/0017/W", "geometry": {
        "type": "Point", "coordinates": [9.633403761462434, 53.67374556296559]}, "properties": {
        "Archivnummer": "2323/0017/W", "X-Koordinate-UTM": 3.254184304E7, "Y-Koordinate-UTM": 5947409.77,
        "Endtiefe-m": 11.5, "LinkzurProfilsäulendarstellung": "http://141.91.161.241/geodin/getportalpage"}}]},
    "MV": {"type": "FeatureCollection", "features": [{"type": "Feature", "id": "bohrdaten.654", "geometry": {
        "type": "Point", "coordinates": [12.053038, 54.108252]}, "properties": {
        "BO_IDENT": 183800879, "LONGNAME": "Hy R 5/1995", "RW": 33307356, "HW": 5999581, "STRAT_EH": None,
        "SVZ_URL": "https://www.umweltkarten.mv-regierung.de/atlas/lbds_svz_overview.php?prj_id=TA6AQC&locid=206",
        "ZCOORDB": 21.75, "ZCOORDE": 8.1}}]},
    "NI": {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {
        "BID": "3624BV0654", "LONGNAME": "BV 654", "OST": 32550000.0, "NORD": 5800000.0, "ZCOORDE": 25.0,
        "LINK": "http://nibis.lbeg.de/DetailseitenKartenserver/DetailSeitenBohrsaeulenGeodin/Bohrungsseite.aspx"}}]},
}


@pytest.mark.parametrize("state", list(STATE_ANSWERS))
def test_state_borehole_points(state):
    [p] = sources.parse_points(state, STATE_ANSWERS[state])
    assert p.name and p.name != "?" and p.depth > 0
    assert 280_000 < p.x < 920_000 and 5_200_000 < p.y < 6_120_000  # Germany in UTM 32N
    if state != "HE":
        assert p.link.startswith("http")
    if state in ("BB", "SH", "MV"):  # the stated coordinates and the lon/lat geometry agree
        x, y = sources._wgs_point(STATE_ANSWERS[state]["features"][0]["geometry"])
        assert abs(p.x - x) < 5 and abs(p.y - y) < 5
    if state == "HE":
        assert "12.9" in p.note and "AQT" in p.note


def test_every_state_is_in_the_overview_and_requests_are_built(monkeypatch):
    assert set(sources.PORTALS) == {s.key for s in states.STATES}
    assert set(sources.POINT_SERVICES) | set(sources.LOG_SERVICES) <= set(sources.PORTALS)
    asked = []

    class Answer:
        def __init__(self, state):
            self.state = state

        def json(self):
            return STATE_ANSWERS[self.state]

    for state, svc in sources.POINT_SERVICES.items():
        monkeypatch.setattr(sources.lookup, "_get", lambda url, params, s=state: asked.append(params) or Answer(s))
        [p] = sources.parse_points(state, STATE_ANSWERS[state])
        found = sources.borehole_points(state, p.x + 30, p.y + 40, 500)
        assert len(found) == 1 and found[0].distance == pytest.approx(50, abs=1)
        assert sources.borehole_points(state, p.x + 3000, p.y, 500) == []
    assert sources.borehole_points("BY", 0, 0, 500) == []
    mv = asked[[*sources.POINT_SERVICES].index("MV") * 2]
    assert mv["BBOX"].startswith("33")  # MV wants the zone in front of the easting


def test_utm33_with_zone_prefix():
    x, y = sources.to_utm32(33_307_356, 5_999_581)
    assert x == pytest.approx(sources.to_utm32(307_356, 5_999_581, 25833)[0])


LOG_TEXT = """Schichtenverzeichnis BK 3/12
0,00 - 0,30 m  Mutterboden, humos
0,30 - 2,10 m  Schluff, tonig,
   feinsandig, braun
2,10 - 8,40 m  Kies, sandig
bis 25,00 m  Tonstein, grau
Ruhewasserspiegel: 3,20 m u. GOK
"""


def test_read_log_text_html_and_pdf():
    from ghe_web.strata import reader
    hole = reader.layers_from_text(LOG_TEXT, "BK", 1.0, 2.0)
    assert [(l.top, l.bottom, l.rock) for l in hole.layers] == [
        (0, 0.3, "Topsoil / humus"), (0.3, 2.1, "Silt / loess"), (2.1, 8.4, "Gravel"),
        (8.4, 25.0, "Claystone / siltstone")]
    assert hole.layers[1].text.endswith("braun") and hole.groundwater == 3.2 and (hole.x, hole.y) == (1.0, 2.0)
    page = "<table><tr><td>0,00</td><td>0,30</td><td>Mutterboden</td></tr><tr><td>0,30</td><td>12,00</td>" \
           "<td>Geschiebemergel</td></tr></table>"
    assert [l.rock for l in reader.layers_from_text(reader.html_text(page)).layers] == \
        ["Topsoil / humus", "Till / boulder clay"]
    with pytest.raises(reader.ReadError):
        reader.layers_from_text("no depths here")
    # a PDF with a text layer is read without the reading service
    import io
    import matplotlib.pyplot as plt
    fig = plt.figure()
    for i, line in enumerate(LOG_TEXT.splitlines()):
        fig.text(0.05, 0.9 - i * 0.08, line)
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf")
    plt.close(fig)
    hole, _ = reader.read_file("log.pdf", buf.getvalue(), 0.0, 0.0)
    assert hole.layers[-1].bottom == 25.0


def test_read_log_picture_with_the_reading_service(monkeypatch):
    from ghe_web.strata import reader
    answer = {"readable": True, "name": "B 7", "groundwater_m": 4.5, "note": "bottom part blurred",
              "layers": [{"top_m": 0, "bottom_m": 1.2, "description": "Auffüllung", "rock": "Unknown"},
                         {"top_m": 1.2, "bottom_m": 9, "description": "mS,g", "rock": "Sand"},
                         {"top_m": 9, "bottom_m": 80, "description": "Granit, verwittert", "rock": "Granite"}]}
    asked = []
    monkeypatch.setattr(reader, "_ask", lambda block: asked.append(block) or answer)
    hole, notes = reader.read_file("shot.png", b"\x89PNG", 5.0, 6.0)
    assert asked[0]["type"] == "image" and asked[0]["source"]["media_type"] == "image/png"
    assert hole.name == "B 7" and hole.groundwater == 4.5 and notes == ["bottom part blurred"]
    assert [l.rock for l in hole.layers] == [rocks.classify("Auffüllung"), "Sand", "Granite"]  # Unknown: by rules
    with pytest.raises(reader.ReadError):
        reader.borehole_from_answer({"readable": False, "note": "a photo of a cat", "layers": []}, "x", 0, 0, "s")
    # without a key, pictures give a clear message instead of a crash
    monkeypatch.undo()
    monkeypatch.setattr(reader, "api_key", lambda: None)
    with pytest.raises(reader.ReadError, match="API key"):
        reader.read_file("shot.png", b"\x89PNG", 0, 0)
    assert set(reader.SCHEMA["properties"]["layers"]["items"]["properties"]["rock"]["enum"]) == set(rocks.NAMES)
