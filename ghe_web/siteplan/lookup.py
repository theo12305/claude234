"""Parcels and buildings from the official open data services of the German states, plus OpenStreetMap.

Everything is converted to ETRS89 / UTM zone 32N (EPSG:25832) in metres. Network errors are raised as
``LookupError_`` with a message for the user; the page then offers the manual routes (upload or draw).
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import requests
import shapely
from pyproj import Transformer
from shapely.geometry import Point, Polygon, shape
from shapely.ops import unary_union

from ..i18n import t
from .states import State, by_key

EPSG = 25832
USER_AGENT = "GHEtool-Web site plan (https://github.com/theo12305/claude234)"
TIMEOUT = 40

_to_utm = Transformer.from_crs(4326, EPSG, always_xy=True)
_to_wgs = Transformer.from_crs(EPSG, 4326, always_xy=True)
_from_crs: dict[int, Transformer] = {}


class LookupError_(RuntimeError):
    """A data service could not answer; the message is meant for the user."""


def to_utm(lon: float, lat: float) -> tuple[float, float]:
    return _to_utm.transform(lon, lat)


def to_wgs84(x: float, y: float) -> tuple[float, float]:
    lon, lat = _to_wgs.transform(x, y)
    return round(lon, 7), round(lat, 7)


def geom_to_wgs84(geom):
    return shapely.transform(geom, lambda xy: _array(_to_wgs.transform(xy[:, 0], xy[:, 1])))


def geom_to_utm(geom, epsg: int = 4326):
    if epsg == EPSG:
        return geom
    tr = Transformer.from_crs(epsg, EPSG, always_xy=True)
    return shapely.transform(geom, lambda xy: _array(tr.transform(xy[:, 0], xy[:, 1])))


def _array(pair):
    import numpy as np
    return np.column_stack(pair)


@dataclass
class Feature:
    geometry: object  # shapely geometry in EPSG:25832
    attrs: dict[str, str] = field(default_factory=dict)


def _get(url: str, params: dict | None = None, data: str | None = None) -> requests.Response:
    try:
        if data is None:
            r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        else:
            r = requests.post(url, data=data.encode(), timeout=TIMEOUT,
                              headers={"User-Agent": USER_AGENT, "Content-Type": "text/xml"})
    except requests.RequestException as exc:
        raise LookupError_(t("The service {host} did not answer ({error}).", host=url.split("/")[2],
                             error=type(exc).__name__)) from exc
    if r.status_code != 200:
        raise LookupError_(t("The service {host} answered with error {code}.", host=url.split("/")[2],
                             code=str(r.status_code)))
    return r


# ---------------------------------------------------------------- finding the place

def geocode(query: str) -> list[dict]:
    """Addresses in Germany matching ``query``: [{"label", "lon", "lat"}]. Uses OpenStreetMap Nominatim."""
    r = _get("https://nominatim.openstreetmap.org/search",
             {"q": query, "format": "jsonv2", "countrycodes": "de", "limit": 6, "addressdetails": 0})
    return [{"label": h["display_name"], "lon": float(h["lon"]), "lat": float(h["lat"])} for h in r.json()]


def state_at(lon: float, lat: float) -> State | None:
    """The Bundesland at a point, from OpenStreetMap Nominatim (reverse geocoding)."""
    r = _get("https://nominatim.openstreetmap.org/reverse",
             {"lon": lon, "lat": lat, "format": "jsonv2", "zoom": 5, "addressdetails": 1})
    address = r.json().get("address", {})
    iso = address.get("ISO3166-2-lvl4", "")
    if not iso.startswith("DE-"):
        return None
    return by_key(iso[3:])


# ---------------------------------------------------------------- GML

_GEOM_TAGS = {"Polygon", "MultiSurface", "MultiPolygon", "Surface", "CompositeSurface"}


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _ring(el) -> list[tuple[float, float]]:
    """The points of a ring; a ring made of several curve segments (ALKIS) is joined segment by segment."""
    pos_lists = [e for e in el.iter() if _local(e.tag) == "posList" and e.text]
    if pos_lists:
        pts: list[tuple[float, float]] = []
        for pos_list in pos_lists:
            nums = [float(v) for v in pos_list.text.split()]
            dim = int(pos_list.get("srsDimension") or pos_list.get("dimension") or 2)
            for i in range(0, len(nums) - dim + 1, dim):
                if not pts or pts[-1] != (nums[i], nums[i + 1]):
                    pts.append((nums[i], nums[i + 1]))
        return pts
    pos = [e for e in el.iter() if _local(e.tag) == "pos"]
    if pos:
        return [tuple(float(v) for v in p.text.split()[:2]) for p in pos]
    coords = next((e for e in el.iter() if _local(e.tag) == "coordinates"), None)
    if coords is not None and coords.text:
        return [tuple(float(v) for v in c.split(",")[:2]) for c in coords.text.split()]
    return []


def _gml_polygons(el) -> list[Polygon]:
    """Every polygon (or polygon patch) below ``el``."""
    out = []
    for e in el.iter():
        if _local(e.tag) not in ("Polygon", "PolygonPatch"):
            continue
        shell, holes = None, []
        for child in e:
            name = _local(child.tag)
            if name in ("exterior", "outerBoundaryIs"):
                shell = _ring(child)
            elif name in ("interior", "innerBoundaryIs"):
                holes.append(_ring(child))
        if shell and len(shell) >= 3:
            out.append(Polygon(shell, [h for h in holes if len(h) >= 3]))
    # curves (arcs) are rare in parcels; a Ring of curve segments is read point by point
    if not out:
        for e in el.iter():
            if _local(e.tag) == "Ring":
                pts = _ring(e)
                if len(pts) >= 3:
                    out.append(Polygon(pts))
    return out


def _fix_axes(geom):
    """Some services send northing first. UTM eastings in Germany are below 1 000 000 m, northings above 5 000 000 m."""
    minx, miny, _, _ = geom.bounds
    if minx > 2_000_000 and miny < 2_000_000:
        return shapely.transform(geom, lambda xy: xy[:, ::-1])
    if 40 < minx < 60 and 2 < miny < 20:  # degrees given as lat, lon
        return shapely.transform(geom, lambda xy: xy[:, ::-1])
    return geom


def parse_gml(content: bytes, epsg: int) -> list[Feature]:
    """Features with polygon geometry from a WFS GetFeature answer (GML 2, 3.1 or 3.2)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise LookupError_(t("The service sent an answer that could not be read.")) from exc
    if _local(root.tag) in ("ExceptionReport", "ServiceExceptionReport"):
        text = " ".join(t.strip() for t in root.itertext() if t.strip())
        raise LookupError_(t("The service reported an error: {error}", error=text[:300]))
    features = []
    for member in root:
        if _local(member.tag) not in ("member", "featureMember", "featureMembers"):
            continue
        for feat in member:
            polys = _gml_polygons(feat)
            if not polys:
                continue
            geom = shapely.make_valid(unary_union(polys) if len(polys) > 1 else polys[0])
            if epsg != EPSG:
                tr = _from_crs.setdefault(epsg, Transformer.from_crs(epsg, EPSG, always_xy=True))
                geom = shapely.transform(_fix_axes(geom), lambda xy: _array(tr.transform(xy[:, 0], xy[:, 1])))
            else:
                geom = _fix_axes(geom)
            attrs = {}
            for e in feat.iter():
                if len(e) == 0 and e.text and e.text.strip() and _local(e.tag) not in ("posList", "pos", "coordinates"):
                    attrs.setdefault(_local(e.tag), e.text.strip())
            features.append(Feature(geom, attrs))
    return features


# ---------------------------------------------------------------- WFS

def _bbox_filter(geom_prop: str, b, epsg: int, version: str) -> str:
    srs = f"urn:ogc:def:crs:EPSG::{epsg}" if version.startswith("2") else f"EPSG:{epsg}"
    gml = "http://www.opengis.net/gml/3.2" if version.startswith("2") else "http://www.opengis.net/gml"
    fes = "http://www.opengis.net/fes/2.0" if version.startswith("2") else "http://www.opengis.net/ogc"
    vr = "ValueReference" if version.startswith("2") else "PropertyName"
    return (f'<fes:Filter xmlns:fes="{fes}" xmlns:gml="{gml}"><fes:BBOX><fes:{vr}>{geom_prop}</fes:{vr}>'
            f'<gml:Envelope srsName="{srs}"><gml:lowerCorner>{b[0]} {b[1]}</gml:lowerCorner>'
            f'<gml:upperCorner>{b[2]} {b[3]}</gml:upperCorner></gml:Envelope></fes:BBOX></fes:Filter>')


def wfs_features(service, bounds_utm, max_features: int = 500) -> list[Feature]:
    """Features of one WFS layer (``service`` from states.py) inside a box given in EPSG:25832."""
    epsg = service.epsg
    if epsg == EPSG:
        b = bounds_utm
    else:
        tr = Transformer.from_crs(EPSG, epsg, always_xy=True)
        b = tr.transform_bounds(*bounds_utm)
    count_key = "COUNT" if service.version.startswith("2") else "MAXFEATURES"
    params = {"SERVICE": "WFS", "VERSION": service.version, "REQUEST": "GetFeature",
              ("TYPENAMES" if service.version.startswith("2") else "TYPENAME"): service.typename,
              "SRSNAME": f"EPSG:{epsg}", count_key: max_features}
    # BBOX with an explicit CRS as the last value keeps the axis order unambiguous
    params["BBOX"] = f"{b[0]:.2f},{b[1]:.2f},{b[2]:.2f},{b[3]:.2f},urn:ogc:def:crs:EPSG::{epsg}" if epsg != 4326 else \
        f"{b[1]:.7f},{b[0]:.7f},{b[3]:.7f},{b[2]:.7f},urn:ogc:def:crs:EPSG::4326"
    params.update(service.extra_params)
    r = _get(service.url, params)
    return parse_gml(r.content, epsg)


NAMESPACES = {"cp": "http://inspire.ec.europa.eu/schemas/cp/4.0",
              "ave": "http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/2.0"}


def wfs_by_attribute(service, prop: str, pattern: str, max_features: int = 50) -> list[Feature]:
    """Features whose ``prop`` matches ``pattern`` (``*`` as wildcard)."""
    v2 = service.version.startswith("2")
    fes = "http://www.opengis.net/fes/2.0" if v2 else "http://www.opengis.net/ogc"
    vr = "ValueReference" if v2 else "PropertyName"
    lit = pattern.replace("&", "&amp;").replace("<", "&lt;")
    prefix = prop.split(":")[0] if ":" in prop else ""
    ns = f' xmlns:{prefix}="{NAMESPACES[prefix]}"' if prefix in NAMESPACES else ""
    filt = (f'<fes:Filter xmlns:fes="{fes}"{ns}><fes:PropertyIsLike wildCard="*" singleChar="?" escapeChar="\\">'
            f'<fes:{vr}>{prop}</fes:{vr}><fes:Literal>{lit}</fes:Literal></fes:PropertyIsLike></fes:Filter>')
    params = {"SERVICE": "WFS", "VERSION": service.version, "REQUEST": "GetFeature",
              ("TYPENAMES" if v2 else "TYPENAME"): service.typename, "SRSNAME": f"EPSG:{service.epsg}",
              ("COUNT" if v2 else "MAXFEATURES"): max_features, "FILTER": filt}
    if prefix in NAMESPACES and v2:
        params["NAMESPACES"] = f"xmlns({prefix},{NAMESPACES[prefix]})"
    params.update(service.extra_params)
    r = _get(service.url, params)
    return parse_gml(r.content, service.epsg)


# ---------------------------------------------------------------- parcels

def _parcel_label(attrs: dict) -> str:
    """"Gemarkung, Flurstück 123/4, Kennzeichen" from the attributes of an INSPIRE or ALKIS parcel."""
    label = attrs.get("label") or ""
    if not label:
        zae = attrs.get("flstnrzae") or attrs.get("zae") or ""
        nen = attrs.get("flstnrnen") or attrs.get("nen") or ""
        label = f"{zae}/{nen}" if zae and nen else zae
    ref = attrs.get("nationalCadastralReference") or attrs.get("flstkennz") or attrs.get("fsko") or ""
    gemarkung = attrs.get("gemarkung") or attrs.get("namgmk") or ""
    parts = [p for p in (gemarkung, f"Flurstück {label}" if label else "", ref) if p]
    return ", ".join(parts) or "Flurstück"


def parcel_at(lon: float, lat: float, state: State | None = None) -> tuple[Feature, State]:
    """The parcel containing the point, from the state's open cadastre service."""
    state = state or state_at(lon, lat)
    if state is None:
        raise LookupError_(t("This point is not in Germany."))
    if state.parcels is None:
        raise LookupError_(t("{state} does not publish its parcels as open data. Upload the parcel outline or "
                             "draw it on the map instead.", state=state.name))
    x, y = to_utm(lon, lat)
    feats = wfs_features(state.parcels, (x - 30, y - 30, x + 30, y + 30), 100)
    pt = Point(x, y)
    hits = [f for f in feats if f.geometry.buffer(0.01).contains(pt)]
    if not hits:
        if not feats:
            raise LookupError_(t("The cadastre of {state} returned no parcel at this point.", state=state.name))
        hits = [min(feats, key=lambda f: f.geometry.distance(pt))]
    feat = min(hits, key=lambda f: f.geometry.area)
    feat.attrs["_label"] = _parcel_label(feat.attrs)
    return feat, state


def flurstueckskennzeichen(state: State, gemarkung: str, flur: str, zaehler: str, nenner: str) -> str:
    """The 14 to 18 leading characters of the 20-character Flurstückskennzeichen (land, Gemarkung, Flur,
    Zähler, Nenner); the rest is matched with a wildcard."""
    g, f, z, n = (re.sub(r"\D", "", s or "") for s in (gemarkung, flur, zaehler, nenner))
    if not g or not z:
        raise LookupError_(t("The Gemarkung number and the Flurstück number (Zähler) are needed."))
    key = f"{state.code}{int(g):04d}{int(f or 0):03d}{int(z):05d}"
    return key + (f"{int(n):04d}" if n else "")


def parcel_by_number(state: State, gemarkung: str, flur: str, zaehler: str, nenner: str) -> list[Feature]:
    if state.parcels is None or not state.parcels.ref_property:
        raise LookupError_(t("Searching by Flurstück number is not available for {state}. Search the address or "
                             "click the parcel on the map instead.", state=state.name))
    key = flurstueckskennzeichen(state, gemarkung, flur, zaehler, nenner)
    feats = wfs_by_attribute(state.parcels, state.parcels.ref_property, key + "*")
    if not feats:  # some states put a prefix (e.g. "DENW") before the number
        feats = wfs_by_attribute(state.parcels, state.parcels.ref_property, "*" + key + "*")
    if not nenner:
        # without a Nenner, prefer the parcel that has none (0000 or ____)
        plain = [f for f in feats if re.search(key + r"(0000|____)", _ref(f))]
        feats = plain or feats
    for f in feats:
        f.attrs["_label"] = _parcel_label(f.attrs)
    return feats


def _ref(f: Feature) -> str:
    return " ".join(f.attrs.values())


# ---------------------------------------------------------------- buildings

def buildings_official(state: State, area_utm) -> list[Feature]:
    if state.buildings is None:
        return []
    b = area_utm.buffer(5).bounds
    return [f for f in wfs_features(state.buildings, b, 1000) if f.geometry.intersects(area_utm.buffer(5))]


OVERPASS = ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter")


def buildings_osm(area_utm) -> list[Feature]:
    """Building outlines from OpenStreetMap around the area."""
    minx, miny, maxx, maxy = area_utm.buffer(10).bounds
    lon0, lat0 = to_wgs84(minx, miny)
    lon1, lat1 = to_wgs84(maxx, maxy)
    query = (f"[out:json][timeout:25];(way[building]({lat0},{lon0},{lat1},{lon1});"
             f"relation[building]({lat0},{lon0},{lat1},{lon1}););out geom;")
    last = None
    for url in OVERPASS:
        try:
            r = _get(url, {"data": query})
            data = r.json()
            break
        except (LookupError_, ValueError) as exc:
            last = exc
    else:
        raise LookupError_(t("OpenStreetMap buildings could not be loaded: {error}", error=last))
    out = []
    for el in data.get("elements", []):
        polys = []
        if el["type"] == "way" and el.get("geometry"):
            pts = [to_utm(p["lon"], p["lat"]) for p in el["geometry"]]
            if len(pts) >= 4:
                polys.append(Polygon(pts))
        elif el["type"] == "relation":
            outers = [[to_utm(p["lon"], p["lat"]) for p in m.get("geometry", [])]
                      for m in el.get("members", []) if m.get("role") == "outer"]
            polys += [Polygon(o) for o in outers if len(o) >= 4]
        for p in polys:
            p = shapely.make_valid(p)
            if p.intersects(area_utm.buffer(10)):
                out.append(Feature(p, {"source": "OpenStreetMap", "building": el.get("tags", {}).get("building", "")}))
    return out


def merge_buildings(official: list[Feature], osm: list[Feature]) -> list[Feature]:
    """Official outlines, plus OpenStreetMap buildings the cadastre does not have (less than half covered)."""
    if not official:
        return osm
    known = unary_union([f.geometry for f in official])
    extra = [f for f in osm if f.geometry.intersection(known).area < 0.5 * f.geometry.area]
    return official + extra


# ---------------------------------------------------------------- files from the user

def read_polygons(name: str, content: bytes) -> list[object]:
    """Polygons from an uploaded GeoJSON, KML or zipped shapefile, converted to EPSG:25832."""
    lower = name.lower()
    if lower.endswith((".geojson", ".json")):
        data = json.loads(content.decode("utf-8-sig"))
        feats = data.get("features", [data]) if data.get("type") == "FeatureCollection" or "features" in data else [data]
        geoms = [shape(f.get("geometry", f)) for f in feats]
        epsg = _geojson_epsg(data)
        return [geom_to_utm(g, epsg) for g in geoms if g.geom_type in ("Polygon", "MultiPolygon")]
    if lower.endswith(".kml"):
        root = ET.fromstring(content)
        polys = _gml_polygons(root)  # KML uses outerBoundaryIs/LinearRing/coordinates like GML 2
        return [geom_to_utm(p, 4326) for p in polys]
    if lower.endswith(".zip"):
        return _read_shapefile_polygons(content)
    raise LookupError_(t("Upload a GeoJSON, KML or zipped shapefile."))


def _geojson_epsg(data: dict) -> int:
    crs = json.dumps(data.get("crs", ""))
    m = re.search(r"EPSG:+(\d+)", crs)
    return int(m.group(1)) if m else 4326


def _read_shapefile_polygons(content: bytes) -> list[object]:
    import io
    import zipfile

    import shapefile  # pyshp
    from pyproj import CRS
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        shp = [n for n in zf.namelist() if n.lower().endswith(".shp") and not n.startswith("__MACOSX")]
        if not shp:
            raise LookupError_(t("The zip file contains no .shp file."))
        stem = shp[0][:-4]
        parts = {n[-3:].lower(): zf.read(n) for n in zf.namelist() if n[:-4] == stem}
    reader = shapefile.Reader(shp=io.BytesIO(parts["shp"]), shx=io.BytesIO(parts["shx"]), dbf=io.BytesIO(parts["dbf"]))
    epsg = EPSG
    if "prj" in parts:
        try:
            epsg = CRS.from_wkt(parts["prj"].decode(errors="ignore")).to_epsg() or EPSG
        except Exception:  # noqa: BLE001 (unknown projection: assume UTM 32N)
            epsg = EPSG
    out = []
    for s in reader.shapes():
        geo = s.__geo_interface__
        if geo["type"] in ("Polygon", "MultiPolygon"):
            out.append(geom_to_utm(shapely.make_valid(shape(geo)), epsg))
    return out


def bounds_ok(geom) -> bool:
    """A sanity check that a geometry lies in Germany (UTM 32N)."""
    minx, miny, maxx, maxy = geom.bounds
    return 0 < minx and maxx < 1_200_000 and 5_200_000 < miny and maxy < 6_150_000

