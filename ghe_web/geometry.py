"""Read borehole positions from GIS files.

Supported: an ESRI shapefile with point (or multipoint) features, uploaded either as
a .zip or as the separate .shp/.shx/.dbf(/.prj) files. Coordinates in degrees
(a geographic .prj, e.g. WGS 84) are converted to metres around the field's centre;
projected coordinates in metres or feet are used as they are.
"""
from __future__ import annotations

import io
import math
import zipfile
from dataclasses import dataclass, field

import shapefile  # pyshp

EARTH_RADIUS = 6_371_000.0  # m
FOOT = 0.3048
POINT_TYPES = {shapefile.POINT, shapefile.POINTZ, shapefile.POINTM,
               shapefile.MULTIPOINT, shapefile.MULTIPOINTZ, shapefile.MULTIPOINTM}


class GeometryError(ValueError):
    """A problem with the uploaded file, worded for the user."""


@dataclass
class ReadResult:
    points: list[tuple[float, float]]  # metres, shifted so the lower left borehole area starts at (0, 0)
    notes: list[str] = field(default_factory=list)


def read_shapefile(files: dict[str, bytes]) -> ReadResult:
    """``files`` maps file names to their content: either one .zip or the shapefile parts."""
    parts = _collect_parts(files)
    for ext in ("shp", "shx", "dbf"):
        if ext not in parts:
            raise GeometryError(f"The .{ext} file is missing. A shapefile needs at least .shp, .shx and .dbf.")

    try:
        reader = shapefile.Reader(shp=io.BytesIO(parts["shp"]), shx=io.BytesIO(parts["shx"]),
                                  dbf=io.BytesIO(parts["dbf"]))
        shapes = reader.shapes()
    except Exception as exc:
        raise GeometryError(f"Could not read the shapefile: {exc}") from exc

    if reader.shapeType not in POINT_TYPES:
        raise GeometryError(f"The shapefile contains {reader.shapeTypeName.lower()} features. "
                            "Each borehole must be a point.")
    raw = [tuple(p[:2]) for s in shapes for p in s.points]
    if not raw:
        raise GeometryError("The shapefile contains no points.")

    notes = []
    prj = parts.get("prj", b"").decode(errors="ignore").strip().upper()
    if not prj:
        notes.append("No .prj file found, so the coordinates are assumed to be in metres.")
        points = raw
    elif prj.startswith("GEOGCS") or prj.startswith("GEOGCRS"):
        points = _degrees_to_metres(raw)
        notes.append("Coordinates were in degrees and have been converted to metres.")
    elif "FOOT" in prj or "FEET" in prj:
        points = [(x * FOOT, y * FOOT) for x, y in raw]
        notes.append("Coordinates were in feet and have been converted to metres.")
    else:
        points = raw

    x0 = min(x for x, _ in points)
    y0 = min(y for _, y in points)
    return ReadResult([(round(x - x0, 3), round(y - y0, 3)) for x, y in points], notes)


def _collect_parts(files: dict[str, bytes]) -> dict[str, bytes]:
    parts: dict[str, bytes] = {}
    for name, content in files.items():
        if name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    shp_names = [n for n in zf.namelist() if n.lower().endswith(".shp")
                                 and not n.startswith("__MACOSX")]
                    if len(shp_names) != 1:
                        raise GeometryError(f"The zip file must contain exactly one .shp file, found {len(shp_names)}.")
                    stem = shp_names[0][:-4]
                    for n in zf.namelist():
                        if n[:-4] == stem:
                            parts[n[-3:].lower()] = zf.read(n)
            except zipfile.BadZipFile as exc:
                raise GeometryError("The zip file could not be opened.") from exc
        else:
            parts[name.rsplit(".", 1)[-1].lower()] = content
    return parts


def _degrees_to_metres(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Local equirectangular projection; accurate to well under 0.1 % over a few kilometres."""
    lat0 = math.radians(sum(lat for _, lat in points) / len(points))
    return [(EARTH_RADIUS * math.radians(lon) * math.cos(lat0), EARTH_RADIUS * math.radians(lat))
            for lon, lat in points]


def closest_pair(points: list[tuple[float, float]]) -> tuple[float, int, int] | None:
    """Smallest distance between two boreholes and their (1-based) numbers."""
    best = None
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = math.dist(points[i], points[j])
            if best is None or d < best[0]:
                best = (d, i + 1, j + 1)
    return best
