"""Where the underground data comes from: open services of the geological surveys and files the user uploads.

- BGR, geological map of Germany 1:250,000 (GÜK250, INSPIRE lithology): the rock at the surface, all of Germany.
- Geologischer Dienst NRW, borehole database (DABO) as BoreholeML web feature service: layered logs of released
  boreholes in North Rhine-Westphalia.
- Borehole points of seven more state surveys (Berlin, Brandenburg, Hessen, Mecklenburg-Vorpommern, Niedersachsen,
  Sachsen, Schleswig-Holstein): location, depth and a link to the log, which these states publish only as a picture
  or web page, so the user reads it and types the layers in.
- Uploads: BoreholeML files (the exchange format of the German state surveys, which most portals export) and
  tables (CSV or Excel) with one row per layer.

Everything is converted to ETRS89 / UTM zone 32N (EPSG:25832) in metres, like the site plan.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import pandas as pd
from pyproj import Transformer

from ..i18n import t
from ..siteplan import lookup
from ..siteplan.lookup import LookupError_
from . import rocks
from .predict import Borehole, LogLayer

GUEK250 = "https://services.bgr.de/arcgis/rest/services/inspire_ge/guek250/MapServer/{layer}/query"
NRW_BML = "https://www.bml3.nrw.de/service/bml"

# Services with layered borehole logs, per state key (as in siteplan.states)
LOG_SERVICES = {"NW": "Geologischer Dienst NRW, borehole database (BoreholeML)"}


# ---------------------------------------------------------------- geological map (BGR)

def surface_geology(x: float, y: float) -> list[dict]:
    """The map units at the point: [{"material", "rock", "age", "process", "role"}], main part first. The
    overlay layer (thin cover such as loess) comes before the base layer."""
    out = []
    for layer in (5, 6):  # GE.GeologicUnit.OverlayLayer.Lithology, ...Baselayer.Lithology
        r = lookup._get(GUEK250.format(layer=layer), {
            "geometry": f"{x},{y}", "geometryType": "esriGeometryPoint", "inSR": lookup.EPSG,
            "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "returnGeometry": "false", "f": "json"})
        data = r.json()
        if "error" in data:
            raise LookupError_(t("The geological map service answered with an error: {error}",
                                 error=data["error"].get("message")))
        for f in data.get("features", []):
            a = f.get("attributes", {})
            material = a.get("material") or a.get("materialPortrayal") or ""
            out.append({"material": material, "rock": rocks.classify(material),
                        "age": " to ".join(dict.fromkeys(v for v in (a.get("olderNamedAge"), a.get("youngerNamedAge"))
                                                         if v)),
                        "process": a.get("eventProcess") or "", "role": a.get("role") or "",
                        "cover": layer == 5})
    order = {"only part": 0, "major part": 1, "dominant constituent": 1, "minor part": 2}
    out.sort(key=lambda u: (not u["cover"], order.get(u["role"], 1)))
    return out


def bedrock_from_map(units: list[dict]) -> str | None:
    """The main rock of the base layer of the map (not the cover), if it could be classified."""
    for u in units:
        if not u["cover"] and u["rock"] != rocks.UNKNOWN:
            return u["rock"]
    return None


# ---------------------------------------------------------------- BoreholeML

def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _find(el, name: str):
    for child in el.iter():
        if _local(child.tag) == name:
            return child
    return None


def _children(el, name: str):
    return [c for c in el.iter() if _local(c.tag) == name]


def _text(el, name: str) -> str:
    found = _find(el, name)
    return (found.text or "").strip() if found is not None and found.text else ""


def _number(text: str) -> float | None:
    try:
        return float(text.replace(",", "."))
    except (AttributeError, ValueError):
        return None


def parse_bml(content: bytes, source: str = "BoreholeML") -> list[Borehole]:
    """Boreholes with layers from a BoreholeML document (a WFS answer or a downloaded file). Boreholes without
    layers are skipped."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise LookupError_(t("This is not a readable BoreholeML file ({error}).", error=exc)) from exc
    if _local(root.tag) in ("ExceptionReport", "ServiceExceptionReport"):
        raise LookupError_(t("The borehole service reported an error: {error}",
                             error=" ".join(root.itertext()).strip()[:200]))
    out = []
    holes = [el for el in root.iter() if _local(el.tag) == "Borehole"]
    for hole in holes:
        layers = []
        for interval in _children(hole, "Interval"):
            top, bottom = _number(_text(interval, "from")), _number(_text(interval, "to"))
            if top is None or bottom is None or bottom <= top:
                continue
            code = _text(interval, "rockCode")
            names = [(_number(_text(lith, "percentageTo")) or 0, _text(lith, "rockName"))
                     for lith in _children(interval, "Lithology")]
            names = [n for _, n in sorted(names, key=lambda t: -t[0]) if n]
            rock = rocks.classify(code)
            if rock == rocks.UNKNOWN:
                for n in names:
                    rock = rocks.classify(n)
                    if rock != rocks.UNKNOWN:
                        break
            layers.append(LogLayer(top, bottom, rock, code or ", ".join(names)))
        if not layers:
            continue
        point = _position(hole)
        if point is None:
            continue
        name = _text(hole, "shortName") or _text(hole, "fullName") or _text(hole, "name") or \
            hole.get("{http://www.opengis.net/gml}id") or hole.get("{http://www.opengis.net/gml/3.2}id") or "Borehole"
        out.append(Borehole(name, point[0], point[1], sorted(layers, key=lambda l: l.top), source))
    return out


def _position(hole) -> tuple[float, float] | None:
    location = _find(hole, "location")
    pos = _find(location if location is not None else hole, "pos")
    if pos is None or not pos.text:
        return None
    values = [float(v) for v in pos.text.split()[:2]]
    srs = pos.get("srsName") or (location.find(".//*[@srsName]").get("srsName")
                                 if location is not None and location.find(".//*[@srsName]") is not None else "")
    epsg = _epsg(srs) or 25832
    if epsg in (5555, 4647):  # UTM 32N with height / with zone prefix
        epsg = 25832
    x, y = values
    if x > 5_000_000 and y < 1_000_000:  # northing first
        x, y = y, x
    if x > 32_000_000:
        x -= 32_000_000
    if epsg == 4326 or (abs(x) <= 90 and abs(y) <= 180):
        lat, lon = (x, y) if epsg == 4326 else (x, y)
        if lat < lon:  # axis order lon, lat
            lat, lon = lon, lat
        return lookup.to_utm(lon, lat)
    if epsg != 25832:
        return Transformer.from_crs(epsg, 25832, always_xy=True).transform(x, y)
    return x, y


def _epsg(srs: str) -> int | None:
    found = re.search(r"(\d{4,5})\s*$", srs or "")
    return int(found.group(1)) if found else None


def nrw_boreholes(x: float, y: float, radius: float, max_features: int = 400) -> list[Borehole]:
    """Logged boreholes around (x, y) from the NRW borehole database. Only released boreholes carry layers."""
    r = lookup._get(NRW_BML, {
        "SERVICE": "WFS", "REQUEST": "GetFeature", "VERSION": "1.1.0", "TYPENAME": "bml:Borehole",
        "MAXFEATURES": max_features, "SRSNAME": "urn:ogc:def:crs:EPSG::25832",
        "BBOX": f"{x - radius},{y - radius},{x + radius},{y + radius},urn:ogc:def:crs:EPSG::25832"})
    return parse_bml(r.content, "GD NRW")


def boreholes_online(state_key: str | None, x: float, y: float, radius: float) -> list[Borehole]:
    if state_key == "NW":
        return nrw_boreholes(x, y, radius)
    return []


# ---------------------------------------------------------------- borehole points of the other states

@dataclass
class BoreholePoint:
    """A borehole of a state survey without machine-readable layers: where it is, how deep, and where to see the
    log (a picture or web page)."""
    name: str
    x: float  # EPSG:25832
    y: float
    depth: float | None
    link: str | None
    source: str
    note: str = ""
    distance: float = 0.0


def _prop(props: dict, *names):
    """The first of the named properties that is set (services rename fields between field names and aliases)."""
    lower = {str(k).lower(): v for k, v in props.items()}
    for n in names:
        v = props.get(n, lower.get(n.lower()))
        if v not in (None, "", "null"):
            return v
    return None


def _float(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def _wgs_point(geometry: dict | None) -> tuple[float, float] | None:
    """The first lon/lat point of a GeoJSON geometry, in UTM 32N."""
    if not geometry:
        return None
    coords = geometry.get("coordinates")
    while isinstance(coords, list) and coords and isinstance(coords[0], list):
        coords = coords[0]
    if not coords or len(coords) < 2:
        return None
    lon, lat = float(coords[0]), float(coords[1])
    if abs(lon) > 180 or abs(lat) > 90:
        return None
    return lookup.to_utm(lon, lat)


@dataclass(frozen=True)
class PointService:
    """One state's borehole points. ``fields`` name the properties: name, depth, link, x, y (with ``epsg``)."""
    state: str
    label: str
    url: str
    kind: str  # "wfs-json", "wfs-gml", "arcgis", "wms-info"
    layer: str
    epsg: int
    fields: dict
    link_note: str
    version: str = "2.0.0"
    output: str = "application/geo+json"


POINT_SERVICES = {s.state: s for s in (
    PointService("BW", "LGRB Baden-Württemberg, borehole database (WFS)", "https://services.lgrb-bw.de/ms/lgrb_adb",
                 "wfs-gml", "ms:adb_et", 25832,
                 {"name": ("Aufschlussname", "Archivnummer"), "depth": ("Tiefe",), "link": (), "x": ("Ost",),
                  "y": ("Nord",), "ref": ("TK25", "Archivnummer"), "logged": ("Schichtdaten",)},
                 "Layer log in LGRBbohrungen (search for the BO number)", output="text/xml; subtype=gml/3.2.1"),
    PointService("BB", "LBGR Brandenburg, borehole points with logs (WFS)", "https://inspire.brandenburg.de/services/bpk_wfs",
                 "wfs-json", "app:bpk_m_sch", 25833,
                 {"name": ("Bohrungsname", "Bohrungs_ID"), "depth": ("Teufe_in_m",),
                  "link": ("Schichtenverzeichnis_grafisch",), "x": ("Ostwert",), "y": ("Nordwert",)},
                 "Log as a picture"),
    PointService("BE", "Berlin, borehole data (WFS)", "https://gdi.berlin.de/services/wfs/bohrdaten",
                 "wfs-json", "bohrdaten:bohrpunkte", 25833,
                 {"name": ("langname", "schluessel"), "depth": ("endteufe",), "link": ("profil_lang", "profil"),
                  "x": ("xcoord",), "y": ("ycoord",)},
                 "Log as a picture", output="application/json"),
    PointService("SN", "LfULG Sachsen, boreholes (ArcGIS)",
                 "https://luis.sachsen.de/arcgis/rest/services/geologie/bohrungen/MapServer/0/query",
                 "arcgis", "0", 25833,
                 {"name": ("AKBEZ", "IDENT"), "depth": ("ENDTEUFE",), "link": ("URL",), "x": (), "y": ()},
                 "Data sheet in the GeODin portal"),
    PointService("HE", "HLNUG Hessen, archive boreholes (ArcGIS)",
                 "https://geodienste-umwelt.hessen.de/arcgis/rest/services/geologie/bohrdatenportal/MapServer/1/query",
                 "arcgis", "1", 25832,
                 {"name": ("ANAME", "Name", "ARNUM", "Archivnummer"), "depth": ("ET", "Endteufe [m]"), "link": (),
                  "x": (), "y": (), "groundwater": ("GW", "Grundwasser angetroffen [m]"),
                  "unit": ("FORMATION", "Geologische Einheit")},
                 "No log online; ask HLNUG for it"),
    PointService("SH", "LfU Schleswig-Holstein, borehole points (WFS)",
                 "https://umweltgeodienste.schleswig-holstein.de/WFS_UWAT", "wfs-json", "app:bohrpunkte", 25832,
                 {"name": ("Archivnummer",), "depth": ("Endtiefe-m",), "link": ("LinkzurProfilsäulendarstellung",),
                  "x": ("X-Koordinate-UTM",), "y": ("Y-Koordinate-UTM",)},
                 "Log column in the GeODin portal"),
    PointService("MV", "LUNG Mecklenburg-Vorpommern, state borehole archive (WFS)",
                 "https://umweltkarten.lung-mv.de/dienste/gg_lbds", "wfs-json", "bohrdaten", 5650,
                 {"name": ("LONGNAME", "BO_IDENT"), "depth": ("ZCOORDE",), "link": ("SVZ_URL",), "x": ("RW",),
                  "y": ("HW",), "unit": ("STRAT_EH",)},
                 "Log (Schichtenverzeichnis) on the LUNG map server", version="1.1.0",
                 output="application/vnd.geo+json"),
    PointService("NI", "LBEG Niedersachsen, NIBIS boreholes (WMS feature info)",
                 "https://nibis.lbeg.de/net3/public/ogc.ashx", "wms-info",
                 ",".join(f"L104:{i}" for i in range(1, 11)), 25832,
                 {"name": ("LONGNAME", "BID"), "depth": ("ZCOORDE",), "link": ("LINK",), "x": ("OST",),
                  "y": ("NORD",)},
                 "Log column in the NIBIS map server", version="1.1.1"),
)}


def _point_request(svc: PointService, x: float, y: float, radius: float, limit: int):
    if svc.epsg == 25832:
        x0, y0, x1, y1 = x - radius, y - radius, x + radius, y + radius
    else:
        tr = Transformer.from_crs(25832, 25833, always_xy=True)
        (x0, x1), (y0, y1) = tr.transform([x - radius, x + radius], [y - radius, y + radius])
    if svc.epsg == 5650:  # UTM 33N with the zone in front of the easting
        x0, x1 = x0 + 33_000_000, x1 + 33_000_000
    if svc.kind == "arcgis":
        return {"geometry": f"{x0},{y0},{x1},{y1}", "geometryType": "esriGeometryEnvelope",
                "inSR": 25833 if svc.epsg != 25832 else 25832, "spatialRel": "esriSpatialRelIntersects",
                "outFields": "*", "returnGeometry": "true", "outSR": 25832, "resultRecordCount": limit, "f": "json"}
    if svc.kind == "wms-info":  # one pixel covering the whole search square returns every point in it
        return {"NodeId": 145, "SERVICE": "WMS", "VERSION": svc.version, "REQUEST": "GetFeatureInfo",
                "LAYERS": svc.layer, "QUERY_LAYERS": svc.layer, "STYLES": "", "SRS": "EPSG:25832",
                "BBOX": f"{x0},{y0},{x1},{y1}", "WIDTH": 1, "HEIGHT": 1, "X": 0, "Y": 0, "FEATURE_COUNT": limit,
                "INFO_FORMAT": "application/geo+json"}
    params = {"SERVICE": "WFS", "VERSION": svc.version, "REQUEST": "GetFeature", "OUTPUTFORMAT": svc.output}
    if svc.version.startswith("2"):
        params |= {"TYPENAMES": svc.layer, "COUNT": limit,
                   "BBOX": f"{x0},{y0},{x1},{y1},urn:ogc:def:crs:EPSG::{svc.epsg}"}
    else:
        params |= {"TYPENAME": svc.layer, "MAXFEATURES": limit, "BBOX": f"{x0},{y0},{x1},{y1}"}
    return params


def gml_features(content: bytes) -> dict:
    """A WFS GML answer as {"features": [{"properties": {...}, "geometry": {"x", "y"}}]} (simple point features)."""
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise LookupError_(t("The borehole service did not answer with data ({error}).", error=exc)) from exc
    if _local(root.tag) in ("ExceptionReport", "ServiceExceptionReport"):
        raise LookupError_(t("The borehole service reported an error: {error}",
                             error=" ".join(root.itertext()).strip()[:200]))
    features = []
    for member in root:
        if _local(member.tag) not in ("member", "featureMember", "featureMembers"):
            continue
        for feature in member:
            props, geometry = {}, {}
            for child in feature:
                pos = _find(child, "pos")
                if pos is not None and pos.text:
                    x, y = (float(v) for v in pos.text.split()[:2])
                    geometry = {"x": x, "y": y}
                elif len(child) == 0:
                    props[_local(child.tag)] = (child.text or "").strip()
            features.append({"properties": props, "geometry": geometry})
    return {"features": features}


def parse_points(state_key: str, data: dict) -> list[BoreholePoint]:
    """Borehole points from a service answer (GeoJSON or ArcGIS JSON), in UTM 32N."""
    svc = POINT_SERVICES[state_key]
    f = svc.fields
    if "error" in data:
        raise LookupError_(t("The borehole service reported an error: {error}",
                             error=str(data["error"].get("message", data["error"]))[:200]))
    out = []
    for feature in data.get("features", []):
        props = feature.get("attributes") if "attributes" in feature else feature.get("properties") or {}
        geom = feature.get("geometry") or {}
        xy = None
        px, py = _float(_prop(props, *f["x"])), _float(_prop(props, *f["y"]))
        if px is not None and py is not None:
            xy = to_utm32(px - (33_000_000 if px > 33_000_000 else 0), py, 25833) if svc.epsg in (25833, 5650) \
                else to_utm32(px, py)
        elif "x" in geom and "y" in geom:  # ArcGIS (asked for in UTM 32N) or GML in the service's system
            xy = float(geom["x"]), float(geom["y"])
        if xy is None:
            xy = _wgs_point(geom)
        if xy is None:
            continue
        name = _prop(props, *f["name"])
        depth = _float(_prop(props, *f["depth"]))
        link = _prop(props, *f["link"]) if f["link"] else None
        notes = []
        if f.get("ref") and all(_prop(props, n) is not None for n in f["ref"]):
            notes.append("BO " + "/".join(str(_prop(props, n)) for n in f["ref"]))
        if f.get("logged"):
            logged = str(_prop(props, *f["logged"])) in ("1", "1.0", "true")
            notes.append(t("layer log in the portal") if logged else t("no layer log"))
            if logged and not link:
                link = PORTALS[state_key][1]
        if f.get("unit") and _prop(props, *f["unit"]):
            notes.append(str(_prop(props, *f["unit"])))
        if f.get("groundwater") and _float(_prop(props, *f["groundwater"])) is not None:
            notes.append(t("groundwater at {gw:.1f} m", gw=_float(_prop(props, *f["groundwater"]))))
        out.append(BoreholePoint(str(name or feature.get("id") or "?"), xy[0], xy[1], depth,
                                 str(link) if link else None, svc.label, ", ".join(notes)))
    return out


def borehole_points(state_key: str | None, x: float, y: float, radius: float, limit: int = 300
                    ) -> list[BoreholePoint]:
    """Boreholes of the state survey within ``radius`` of the site, nearest first."""
    svc = POINT_SERVICES.get(state_key or "")
    if svc is None:
        return []
    r = lookup._get(svc.url, _point_request(svc, x, y, radius, limit))
    if svc.kind == "wfs-gml":
        return _near(parse_points(state_key, gml_features(r.content)), x, y, radius)
    try:
        data = r.json()
    except ValueError as exc:
        raise LookupError_(t("The borehole service did not answer with data ({error}).",
                             error=r.text.strip()[:120] or type(exc).__name__)) from exc
    return _near(parse_points(state_key, data), x, y, radius)


def _near(points: list[BoreholePoint], x: float, y: float, radius: float) -> list[BoreholePoint]:
    for p in points:
        p.distance = ((p.x - x) ** 2 + (p.y - y) ** 2) ** 0.5
    return sorted((p for p in points if p.distance <= radius), key=lambda p: p.distance)


# What each state survey offers, for the page's overview (state key -> survey, portal, what is open)
PORTALS = {
    "BW": ("LGRB Baden-Württemberg (LGRBbohrungen)", "https://bohrungen.lgrb-bw.de",
           "Connected: boreholes with depth and BO number; layer logs in LGRBbohrungen."),
    "BY": ("LfU Bayern", "https://www.umweltatlas.bayern.de",
           "Boreholes in the UmweltAtlas (Geologie); no open download service."),
    "BE": ("Senatsverwaltung Berlin", "https://gdi.berlin.de",
           "Connected: boreholes with a picture of the log."),
    "BB": ("LBGR Brandenburg", "https://lbgr.brandenburg.de",
           "Connected: boreholes with a picture of the log."),
    "HB": ("Geologischer Dienst für Bremen", "https://www.gdfb.de",
           "No open borehole service found; ask the survey."),
    "HH": ("Geologisches Landesamt Hamburg",
           "https://www.hamburg.de/politik-und-verwaltung/behoerden/bukea/themen/boden-und-geologie/geologie/"
           "geologische-daten-und-archiv", "No open borehole service found; ask the survey."),
    "HE": ("HLNUG Hessen", "https://www.hlnug.de",
           "Connected: archive boreholes with depth, unit and groundwater; logs on request."),
    "MV": ("LUNG Mecklenburg-Vorpommern", "https://www.umweltkarten.mv-regierung.de",
           "Connected: boreholes with a link to the released log."),
    "NI": ("LBEG Niedersachsen (NIBIS)", "https://nibis.lbeg.de/cardomap3/",
           "Connected: boreholes with a picture of the log column."),
    "NW": ("Geologischer Dienst NRW", "https://www.gd.nrw.de",
           "Connected: logs with layers (BoreholeML), used for the prediction directly."),
    "RP": ("LGB Rheinland-Pfalz", "https://www.lgb-rlp.de",
           "Boreholes in the LGB map viewer; no open download service."),
    "SL": ("LUA Saarland", "https://www.saarland.de/lvgl/DE/GeoportalSaarland/geoportalsaarland_node",
           "No open borehole service found; ask the survey."),
    "SN": ("LfULG Sachsen", "https://www.umwelt.sachsen.de",
           "Connected: boreholes with a data sheet link."),
    "ST": ("LAGB Sachsen-Anhalt", "https://lagb.sachsen-anhalt.de/service/landesbohrdatenbank/",
           "Map of the state borehole database; logs on request."),
    "SH": ("LfU Schleswig-Holstein", "https://umweltportal.schleswig-holstein.de/portal/",
           "Connected: boreholes with a link to the log column."),
    "TH": ("TLUBN Thüringen", "https://tlubn.thueringen.de",
           "No open borehole service found; ask the survey."),
}


# ---------------------------------------------------------------- tables

_ALIASES = {
    "name": ("borehole", "bohrung", "name", "id", "bezeichnung", "bohrpunkt", "aufschluss"),
    "x": ("x", "easting", "east", "rechtswert", "ostwert", "utm_x", "e"),
    "y": ("y", "northing", "north", "hochwert", "nordwert", "utm_y", "n"),
    "lon": ("lon", "longitude", "lng", "länge", "laenge"),
    "lat": ("lat", "latitude", "breite"),
    "top": ("top", "from", "von", "oberkante", "depth_top", "top_m", "von_m", "ok"),
    "bottom": ("bottom", "to", "bis", "unterkante", "depth_bottom", "bottom_m", "bis_m", "uk", "depth", "tiefe"),
    "text": ("description", "rock", "lithology", "petrographie", "petrography", "gestein", "beschreibung", "code",
             "schicht", "material", "sep3", "rock_type", "bodenart"),
    "groundwater": ("groundwater", "grundwasser", "gw", "groundwater_m", "gw_m", "wasserstand"),
}
EPSG_CHOICES = {"Detect automatically": None, "ETRS89 / UTM 32N (EPSG:25832)": 25832,
                "ETRS89 / UTM 33N (EPSG:25833)": 25833, "Gauß-Krüger zone 2 (EPSG:31466)": 31466,
                "Gauß-Krüger zone 3 (EPSG:31467)": 31467, "Gauß-Krüger zone 4 (EPSG:31468)": 31468,
                "Gauß-Krüger zone 5 (EPSG:31469)": 31469, "WGS84 longitude/latitude (EPSG:4326)": 4326}


class TableError(ValueError):
    """The uploaded table could not be read; the message is meant for the user."""


def _column(df: pd.DataFrame, role: str) -> str | None:
    norm = {re.sub(r"[\s\[\]()]+", "_", str(c).strip().lower()).strip("_"): c for c in df.columns}
    for alias in _ALIASES[role]:
        if alias in norm:
            return norm[alias]
    for alias in _ALIASES[role]:  # "Top [m]" -> "top_m"; "Depth top" -> "depth_top"
        for key, col in norm.items():
            if len(alias) > 2 and key.startswith(alias + "_"):
                return col
    return None


def read_table(name: str, content: bytes, epsg: int | None = None, site: tuple[float, float] | None = None
               ) -> tuple[list[Borehole], list[str]]:
    """Boreholes from a table with one row per layer. Columns (German or English names): borehole name,
    coordinates (x/y or lon/lat), top and bottom depth in m, and the description or SEP 3 code. Rows without
    coordinates belong to a borehole on the site itself."""
    try:
        if name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            text = content.decode("utf-8-sig", errors="replace")
            df = pd.read_csv(io.StringIO(text), sep=None, engine="python")
    except Exception as exc:
        raise TableError(t("Could not read {name}: {error}", name=name, error=exc)) from exc
    cols = {role: _column(df, role) for role in _ALIASES}
    if cols["bottom"] is None or cols["text"] is None:
        raise TableError(t("The table needs at least a column for the bottom depth (e.g. 'bottom' or 'bis') and "
                           "one for the rock (e.g. 'description', 'petrographie' or 'code'). Download the template."))
    notes = []
    df = df.copy()
    for role in ("x", "y", "lon", "lat", "top", "bottom", "groundwater"):
        if cols[role] is not None:
            df[cols[role]] = pd.to_numeric(df[cols[role]].astype(str).str.replace(",", ".").str.strip(),
                                           errors="coerce")
    name_col = cols["name"]
    if name_col is None:
        df["_name"] = "Borehole 1"
        name_col = "_name"
    df[name_col] = df[name_col].ffill().astype(str)
    out = []
    for hole_name, rows in df.groupby(name_col, sort=False):
        rows = rows.dropna(subset=[cols["bottom"]]).sort_values(cols["bottom"])
        if rows.empty:
            continue
        layers, top = [], 0.0
        for _, row in rows.iterrows():
            bottom = float(row[cols["bottom"]])
            if cols["top"] is not None and pd.notna(row[cols["top"]]):
                top = float(row[cols["top"]])
            if bottom <= top:
                continue
            text = str(row[cols["text"]]) if pd.notna(row[cols["text"]]) else ""
            layers.append(LogLayer(top, bottom, rocks.classify(text), text))
            top = bottom
        xy = _table_position(rows, cols, epsg)
        if xy is None:
            if site is None:
                raise TableError(t("Borehole {name} has no coordinates. Set the site location first, or add x and y "
                                   "columns.", name=hole_name))
            xy = site
            notes.append(t("{name}: no coordinates, so it is placed on the site.", name=hole_name))
        gw = None
        if cols["groundwater"] is not None:
            levels = rows[cols["groundwater"]].dropna()
            gw = float(levels.iloc[0]) if len(levels) else None
        out.append(Borehole(str(hole_name), xy[0], xy[1], layers, f"upload ({name})", gw))
    unknown = sorted({l.text for b in out for l in b.layers if l.rock == rocks.UNKNOWN and l.text})
    if unknown:
        notes.append(t("Not recognised (set to Unknown, k = 2.0 W/(m·K)): {which}",
                       which=", ".join(unknown[:8]) + (" ..." if len(unknown) > 8 else "")))
    if not out:
        raise TableError(t("No layers found in the table."))
    return out, notes


def _table_position(rows, cols, epsg):
    def first(role):
        if cols[role] is None:
            return None
        values = rows[cols[role]].dropna()
        return float(values.iloc[0]) if len(values) else None
    lon, lat = first("lon"), first("lat")
    if lon is not None and lat is not None:
        return lookup.to_utm(lon, lat)
    x, y = first("x"), first("y")
    if x is None or y is None:
        return None
    return to_utm32(x, y, epsg)


def to_utm32(x: float, y: float, epsg: int | None = None) -> tuple[float, float]:
    """Coordinates in a German system to EPSG:25832. Without epsg the system is guessed from the numbers."""
    if epsg is None:
        if abs(x) <= 180 and abs(y) <= 90:
            epsg = 4326
        elif x > 33_000_000:
            x, epsg = x - 33_000_000, 25833
        elif x > 32_000_000:
            x, epsg = x - 32_000_000, 25832
        elif 2_000_000 < x < 6_000_000 and 5_000_000 < y < 6_200_000:
            epsg = 31464 + int(x // 1_000_000)
        else:
            epsg = 25832
    if epsg == 25832:
        return x, y
    if epsg == 4326:
        return lookup.to_utm(x, y)
    return Transformer.from_crs(epsg, 25832, always_xy=True).transform(x, y)


def template_csv() -> bytes:
    rows = [("BH 1", 32350120.0, 5645230.0, 0.0, 0.4, "Mu", 3.5), ("BH 1", "", "", 0.4, 6.0, "Sand, kiesig", ""),
            ("BH 1", "", "", 6.0, 18.0, "Kies", ""), ("BH 1", "", "", 18.0, 120.0, "Tonstein", ""),
            ("BH 2", 32350410.0, 5645010.0, 0.0, 8.0, "mS,g", ""), ("BH 2", "", "", 8.0, 95.0, "Tst", "")]
    df = pd.DataFrame(rows, columns=["borehole", "x", "y", "top", "bottom", "description", "groundwater"])
    return df.to_csv(index=False, sep=";").encode()
