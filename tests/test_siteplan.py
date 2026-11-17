import io
import zipfile

import pytest
from shapely.geometry import Polygon, box

from ghe_web import geometry
from ghe_web.siteplan import export, lookup
from ghe_web.siteplan.layout import Rules, Site, allowed_area, check, place_boreholes
from ghe_web.siteplan.states import STATES

# a 60 m x 40 m parcel near Aachen, in UTM 32N, with a house in it
X0, Y0 = 294_000.0, 5_628_000.0
PARCEL = box(X0, Y0, X0 + 60, Y0 + 40)
HOUSE = box(X0 + 10, Y0 + 10, X0 + 22, Y0 + 22)


def test_allowed_area_keeps_the_distances():
    area = allowed_area(Site(PARCEL, [HOUSE]), Rules(border_distance=3, building_distance=2))
    assert area.area == pytest.approx(54 * 34 - 16 * 16, abs=5)  # house + 2 m has rounded corners
    assert area.distance(HOUSE) == pytest.approx(2, abs=0.01)
    assert PARCEL.exterior.distance(area) == pytest.approx(3, abs=0.01)


def test_placement_respects_every_rule_and_beats_a_plain_grid():
    site, rules = Site(PARCEL, [HOUSE]), Rules(border_distance=3, building_distance=2, spacing=6)
    placed = place_boreholes(allowed_area(site, rules), rules.spacing)
    assert check(placed.points, site, rules) == []
    # a plain 6 m square grid from the corner of the allowed area fits 10 x 6 = 60 minus the house
    assert len(placed.points) >= 60


def test_irregular_parcel_with_holes():
    parcel = Polygon([(0, 0), (52, 0), (60, 30), (20, 48), (0, 35)])
    site = Site(parcel, [box(20, 10, 35, 25)], [box(0, 30, 10, 40)])
    rules = Rules(border_distance=3, building_distance=2, spacing=6, exclusion_distance=1)
    placed = place_boreholes(allowed_area(site, rules), rules.spacing)
    assert len(placed.points) > 30
    assert check(placed.points, site, rules) == []


def test_limit_and_empty_area():
    area = allowed_area(Site(PARCEL), Rules())
    assert len(place_boreholes(area, 6, max_count=10).points) == 10
    assert place_boreholes(allowed_area(Site(box(0, 0, 5, 5)), Rules(border_distance=3)), 6).points == []


def test_check_finds_problems():
    site, rules = Site(PARCEL, [HOUSE]), Rules(spacing=6)
    problems = check([(X0 + 1, Y0 + 20), (X0 + 30, Y0 + 20), (X0 + 33, Y0 + 20)], site, rules)
    assert len(problems) == 2


def test_borehole_zip_loads_in_the_borefield_step():
    pts = [(X0 + 5, Y0 + 5), (X0 + 11, Y0 + 5), (X0 + 5, Y0 + 11)]
    data = export.borehole_zip(pts, 6)
    read = geometry.read_shapefile({"bhe.zip": data})
    assert read.points == [(0.0, 0.0), (6.0, 0.0), (0.0, 6.0)]


def test_project_zip_contents():
    site, rules = Site(PARCEL, [HOUSE], [box(X0 + 40, Y0, X0 + 45, Y0 + 5)]), Rules()
    pts = place_boreholes(allowed_area(site, rules), 6).points
    data = export.project_zip(site, rules, pts, {"Parcel": "Test"}, ("https://example.org/wms", "dop"))
    names = set(zipfile.ZipFile(io.BytesIO(data)).namelist())
    for stem in ("bhe_positions", "parcel", "buildings", "exclusions", "allowed_area"):
        assert {f"{stem}.shp", f"{stem}.shx", f"{stem}.dbf", f"{stem}.prj"} <= names
    assert {"site_plan.png", "site_plan.qgs", "README.txt"} <= names
    qgs = zipfile.ZipFile(io.BytesIO(data)).read("site_plan.qgs").decode()
    assert "bhe_positions.shp" in qgs and "EPSG:25832" in qgs


def test_polygon_shapefile_round_trip():
    pts = place_boreholes(allowed_area(Site(PARCEL), Rules()), 6).points
    data = export.project_zip(Site(PARCEL), Rules(), pts, {})
    zf = zipfile.ZipFile(io.BytesIO(data))
    parcel_zip = io.BytesIO()
    with zipfile.ZipFile(parcel_zip, "w") as out:
        for n in zf.namelist():
            if n.startswith("parcel."):
                out.writestr(n, zf.read(n))
    polys = lookup.read_polygons("parcel.zip", parcel_zip.getvalue())
    assert polys[0].area == pytest.approx(PARCEL.area, rel=1e-6)
    assert polys[0].bounds == pytest.approx(PARCEL.bounds)


GML = b"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
  xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0">
 <wfs:member><cp:CadastralParcel gml:id="p1">
  <cp:geometry><gml:MultiSurface><gml:surfaceMember><gml:Polygon>
   <gml:exterior><gml:LinearRing><gml:posList srsDimension="2">
    294000 5628000 294060 5628000 294060 5628040 294000 5628040 294000 5628000</gml:posList></gml:LinearRing></gml:exterior>
  </gml:Polygon></gml:surfaceMember></gml:MultiSurface></cp:geometry>
  <cp:label>123/4</cp:label><cp:nationalCadastralReference>05123400100123000400</cp:nationalCadastralReference>
 </cp:CadastralParcel></wfs:member>
</wfs:FeatureCollection>"""


def test_parse_inspire_gml():
    feats = lookup.parse_gml(GML, 25832)
    assert len(feats) == 1
    assert feats[0].geometry.area == pytest.approx(2400)
    assert feats[0].attrs["label"] == "123/4"
    assert "123/4" in lookup._parcel_label(feats[0].attrs)


def test_parse_gml_northing_first_and_other_zone():
    swapped = GML.replace(b"294000 5628000 294060 5628000 294060 5628040 294000 5628040 294000 5628000",
                          b"5628000 294000 5628000 294060 5628040 294060 5628040 294000 5628000 294000")
    assert lookup.parse_gml(swapped, 25832)[0].geometry.bounds == pytest.approx(PARCEL.bounds)
    # the same parcel given in UTM 33N comes back in UTM 32N
    x, y = lookup.to_utm(13.4, 52.5)
    from pyproj import Transformer
    x33, y33 = Transformer.from_crs(25832, 25833, always_xy=True).transform(x, y)
    gml33 = GML.replace(b"294000 5628000 294060 5628000 294060 5628040 294000 5628040 294000 5628000",
                        f"{x33} {y33} {x33 + 50} {y33} {x33 + 50} {y33 + 50} {x33} {y33 + 50} {x33} {y33}".encode())
    geom = lookup.parse_gml(gml33, 25833)[0].geometry
    assert geom.exterior.coords[0] == pytest.approx((x, y), abs=0.01)
    assert geom.area == pytest.approx(2500, rel=0.01)


def test_service_error_is_reported():
    report = b'<ows:ExceptionReport xmlns:ows="http://www.opengis.net/ows/1.1"><ows:Exception><ows:ExceptionText>' \
             b'bad typename</ows:ExceptionText></ows:Exception></ows:ExceptionReport>'
    with pytest.raises(lookup.LookupError_, match="bad typename"):
        lookup.parse_gml(report, 25832)


def test_flurstueckskennzeichen():
    nw = next(s for s in STATES if s.key == "NW")
    assert lookup.flurstueckskennzeichen(nw, "1234", "1", "123", "4") == "05123400100123" + "0004"
    assert lookup.flurstueckskennzeichen(nw, "1234", "", "56", "") == "051234???00056"


def test_every_state_is_configured():
    assert len(STATES) == 16
    assert len({s.code for s in STATES}) == 16
    for s in STATES:
        assert s.border_distance >= 0 and s.border_note


ALKIS = b"""<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
  xmlns:ave="http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0">
 <wfs:member><ave:Flurstueck gml:id="f1"><ave:geometrie><gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior>
  <gml:Ring>
   <gml:curveMember><gml:LineString><gml:posList>294000 5628000 294060 5628000</gml:posList></gml:LineString></gml:curveMember>
   <gml:curveMember><gml:LineString><gml:posList>294060 5628000 294060 5628040 294000 5628040</gml:posList></gml:LineString></gml:curveMember>
   <gml:curveMember><gml:LineString><gml:posList>294000 5628040 294000 5628000</gml:posList></gml:LineString></gml:curveMember>
  </gml:Ring></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface></ave:geometrie>
  <ave:gemarkung>Musterdorf</ave:gemarkung><ave:flstnrzae>123</ave:flstnrzae><ave:flstnrnen>4</ave:flstnrnen>
 </ave:Flurstueck></wfs:member>
</wfs:FeatureCollection>"""


def test_parse_alkis_ring_of_segments():
    feat = lookup.parse_gml(ALKIS, 25832)[0]
    assert feat.geometry.area == pytest.approx(2400)
    assert lookup._parcel_label(feat.attrs) == "Musterdorf, Flurstück 123/4"


def test_parcel_at_asks_the_state_service(monkeypatch):
    seen = {}

    class Answer:
        status_code, content, headers = 200, GML, {"Content-Type": "application/gml+xml"}

    class FakeSession:
        def get(self, url, params=None, **kw):
            seen.update(url=url, params=params)
            return Answer()

    monkeypatch.setattr(lookup, "_session", FakeSession)
    nw = next(s for s in STATES if s.key == "NW")
    lon, lat = lookup.to_wgs84(X0 + 30, Y0 + 20)
    feat, state = lookup.parcel_at(lon, lat, nw)
    assert state is nw and feat.geometry.area == pytest.approx(2400)
    assert seen["url"] == nw.parcels.url and seen["params"]["TYPENAMES"] == "cp:CadastralParcel"
    assert seen["params"]["BBOX"].endswith("urn:ogc:def:crs:EPSG::25832")


def test_the_first_mirror_that_answers_wins():
    import time

    def fetch(url):
        if url == "slow":
            time.sleep(2)
            return "slow"
        if url == "broken":
            raise lookup.LookupError_("down")
        return "fast"
    start = time.time()
    assert lookup._first_answer(fetch, ["slow", "broken", "fast"], "none: {error}") == "fast"
    assert time.time() - start < 1.5
    with pytest.raises(lookup.LookupError_, match="none: down"):
        lookup._first_answer(fetch, ["broken"], "none: {error}")


# ---------------------------------------------------------------- second route to a parcel (BW, 2026-11)

_MAPSERVER_GML = b"""<?xml version="1.0" encoding="UTF-8"?>
<msGMLOutput xmlns:gml="http://www.opengis.net/gml">
 <CadastralParcel_layer><CadastralParcel_feature>
  <gml:boundedBy><gml:Box srsName="EPSG:25832"><gml:coordinates>513400,5402500 513460,5402560</gml:coordinates></gml:Box></gml:boundedBy>
  <geometry><gml:Polygon srsName="EPSG:25832"><gml:outerBoundaryIs><gml:LinearRing>
   <gml:coordinates>513400,5402500 513460,5402500 513460,5402560 513400,5402560 513400,5402500</gml:coordinates>
  </gml:LinearRing></gml:outerBoundaryIs></gml:Polygon></geometry>
  <label>366/2</label><nationalCadastralReference>0811110010036600002</nationalCadastralReference>
 </CadastralParcel_feature></CadastralParcel_layer>
</msGMLOutput>"""

_GML3 = b"""<?xml version="1.0" encoding="UTF-8"?>
<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs" xmlns:gml="http://www.opengis.net/gml"
  xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0">
 <gml:featureMember><cp:CadastralParcel>
  <cp:geometry><gml:MultiSurface><gml:surfaceMember><gml:Polygon><gml:exterior><gml:LinearRing>
   <gml:posList srsDimension="2">513400 5402500 513460 5402500 513460 5402560 513400 5402500</gml:posList>
  </gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember></gml:MultiSurface></cp:geometry>
  <cp:label>12</cp:label>
 </cp:CadastralParcel></gml:featureMember>
</wfs:FeatureCollection>"""


def test_feature_info_gml_of_both_server_kinds():
    a = lookup.gml_features_anywhere(_MAPSERVER_GML, 25832)
    assert len(a) == 1 and a[0].geometry.area == pytest.approx(3600)
    assert a[0].attrs["label"] == "366/2" and "coordinates" not in a[0].attrs
    b = lookup.gml_features_anywhere(_GML3, 25832)
    assert len(b) == 1 and b[0].geometry.area == pytest.approx(1800) and b[0].attrs["label"] == "12"


def test_parcel_falls_back_to_the_map_service_when_the_wfs_fails(monkeypatch):
    bw = next(s for s in STATES if s.key == "BW")
    assert bw.parcel_info is not None and bw.overlay is not None

    def broken(*args, **kwargs):
        raise lookup.LookupError_("The service owsproxy.lgl-bw.de answered with error 503.")

    monkeypatch.setattr(lookup, "wfs_features", broken)
    monkeypatch.setattr(lookup, "parcel_info_at", lambda wms, x, y: lookup.gml_features_anywhere(_MAPSERVER_GML, 25832))
    lon, lat = lookup.to_wgs84(513430, 5402530)
    feat, state = lookup.parcel_at(lon, lat, bw)
    assert state.key == "BW" and feat.geometry.area == pytest.approx(3600)
    assert "366/2" in feat.attrs["_label"]

    def also_broken(*args, **kwargs):
        raise lookup.LookupError_("no")

    monkeypatch.setattr(lookup, "parcel_info_at", also_broken)
    monkeypatch.setattr(lookup, "parcel_from_map", also_broken)
    with pytest.raises(lookup.LookupError_, match="error 503.*parcel lines"):
        lookup.parcel_at(lon, lat, bw)


def test_firewall_page_is_reported(monkeypatch):
    class Answer:
        status_code = 200
        headers = {"Content-Type": "text/html; charset=utf-8"}
        content = b"<html><head><title>Request Rejected</title></head><body>The requested URL was rejected.</body></html>"

    class Session:
        def get(self, *a, **k):
            return Answer()

    monkeypatch.setattr(lookup, "_session", lambda: Session())
    with pytest.raises(lookup.LookupError_, match="refused the request"):
        lookup._get("https://owsproxy.lgl-bw.de/owsproxy/wfs/x", {})


def _parcel_map(size=600):
    """A transparent parcel-line map: a 30 m x 20 m parcel at the centre (0.2 m per pixel), a number inside it, and
    a neighbour to the east."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size // 2
    d.rectangle([c - 75, c - 50, c + 75, c + 50], outline=(200, 30, 30, 255), width=2)  # 30 m x 20 m
    d.rectangle([c + 75, c - 50, c + 175, c + 50], outline=(200, 30, 30, 255), width=2)
    d.text((c - 10, c - 5), "366/2", fill=(0, 0, 0, 255))
    return img


def test_parcel_is_traced_from_the_parcel_lines():
    bbox = (513430 - 60, 5402530 - 60, 513430 + 60, 5402530 + 60)
    poly = lookup.trace_parcel(_parcel_map(), bbox)
    assert poly is not None and poly.area == pytest.approx(600, rel=0.05)
    assert poly.contains(lookup.Point(513430, 5402530))
    minx, miny, maxx, maxy = poly.bounds
    assert maxx - minx == pytest.approx(30, abs=0.6) and maxy - miny == pytest.approx(20, abs=0.6)
    # no closed line around the point: nothing
    from PIL import Image
    assert lookup.trace_parcel(Image.new("RGBA", (600, 600), (0, 0, 0, 0)), bbox) is None


def test_bayern_parcel_comes_from_the_parcel_map(monkeypatch):
    import io
    by = next(s for s in STATES if s.key == "BY")
    buf = io.BytesIO()
    _parcel_map().save(buf, "PNG")

    class Answer:
        status_code, content, headers = 200, buf.getvalue(), {"Content-Type": "image/png"}

    class Session:
        def get(self, url, params=None, **kw):
            assert params["REQUEST"] == "GetMap" and params["LAYERS"] == by.overlay.layer
            return Answer()

    monkeypatch.setattr(lookup, "_session", lambda: Session())
    lon, lat = lookup.to_wgs84(600000, 5400000)
    feat, state = lookup.parcel_at(lon, lat, by)
    assert state.key == "BY" and feat.attrs[lookup.TRACED] == "1"
    assert feat.geometry.area == pytest.approx(600, rel=0.05)
