"""Where the underground data comes from: open services of the geological surveys and files the user uploads.

- BGR, geological map of Germany 1:250,000 (GÜK250, INSPIRE lithology): the rock at the surface, all of Germany.
- Geologischer Dienst NRW, borehole database (DABO) as BoreholeML web feature service: layered logs of released
  boreholes in North Rhine-Westphalia.
- Uploads: BoreholeML files (the exchange format of the German state surveys, which most portals export) and
  tables (CSV or Excel) with one row per layer.

Everything is converted to ETRS89 / UTM zone 32N (EPSG:25832) in metres, like the site plan.
"""
from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET

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
        elif x > 32_000_000:
            x, epsg = x - 32_000_000, 25832
        elif x > 33_000_000:
            x, epsg = x - 33_000_000, 25833
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
