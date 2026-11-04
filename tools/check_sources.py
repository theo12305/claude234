"""Checks every external data service and link of the app, state by state, and prints a status table.

Run: python tools/check_sources.py  (about 1 to 3 minutes; needs internet). Writes source_status.md and .json.
Each state is tested at a built-up point (a city centre), using the same functions the app calls.
"""
from __future__ import annotations

import io
import json
import math
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shapely.geometry import box  # noqa: E402

from ghe_web.siteplan import lookup  # noqa: E402
from ghe_web.siteplan.states import STATES  # noqa: E402
from ghe_web.strata import sources  # noqa: E402

POINTS = {  # lon, lat of a built-up spot in each state
    "SH": (10.1355, 54.3216), "HH": (9.9937, 53.5511), "NI": (9.7320, 52.3759), "HB": (8.8017, 53.0793),
    "NW": (6.9603, 50.9375), "HE": (8.6821, 50.1109), "RP": (8.2473, 49.9929), "BW": (9.1829, 48.7758),
    "BY": (11.5755, 48.1374), "SL": (6.9969, 49.2402), "BE": (13.4050, 52.5200), "BB": (13.0645, 52.3906),
    "MV": (11.4148, 53.6288), "SN": (13.7373, 51.0504), "ST": (11.6276, 52.1205), "TH": (11.0299, 50.9848),
}


def timed(fn):
    t0 = time.time()
    try:
        detail = fn()
        return {"ok": True, "detail": detail, "s": round(time.time() - t0, 1)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "detail": f"{type(exc).__name__}: {str(exc)[:220]}", "s": round(time.time() - t0, 1)}


def wms_tile(wms, lon, lat):
    """A 256 px GetMap in web mercator around the point, as the map in the browser asks for it."""
    from PIL import Image
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) * 20037508.34 / math.pi
    h = 150
    crs_key = "CRS" if wms.version.startswith("1.3") else "SRS"
    r = lookup._session().get(wms.url, params={
        "SERVICE": "WMS", "VERSION": wms.version, "REQUEST": "GetMap", "LAYERS": wms.layer, "STYLES": "",
        crs_key: "EPSG:3857", "BBOX": f"{x - h},{y - h},{x + h},{y + h}", "WIDTH": 256, "HEIGHT": 256,
        "FORMAT": wms.format, "TRANSPARENT": "TRUE"}, timeout=40)
    ctype = r.headers.get("Content-Type", "")
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}")
    if not ctype.startswith("image"):
        raise RuntimeError(f"no image ({ctype}): {r.text.strip()[:160]}")
    img = Image.open(io.BytesIO(r.content)).convert("RGBA")
    colors = len(img.getcolors(256 * 256) or [])
    if colors <= 2:
        raise RuntimeError(f"blank image ({colors} colours)")
    return f"image, {colors} colours"


def link(url):
    r = lookup._session().get(url, timeout=30, allow_redirects=True)
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}")
    moved = f" -> {r.url}" if r.url.rstrip("/") != url.rstrip("/") else ""
    return f"HTTP {r.status_code}{moved}"


def _geology(x, y):
    units = sources.surface_geology(x, y)
    if not units:
        raise RuntimeError("no map unit at the point")
    return ", ".join(u["material"] for u in units)[:80]


def check_state(state):
    lon, lat = POINTS[state.key]
    x, y = lookup.to_utm(lon, lat)
    out = {"name": state.name}
    if state.parcels:
        out["parcels"] = timed(lambda: lookup.parcel_at(lon, lat, state)[0].attrs["_label"])
    if state.buildings:
        out["buildings"] = timed(lambda: f"{len(lookup.buildings_official(state, box(x - 60, y - 60, x + 60, y + 60)))} buildings")
    if state.imagery:
        out["imagery"] = timed(lambda: wms_tile(state.imagery, lon, lat))
    if state.overlay:
        out["overlay"] = timed(lambda: wms_tile(state.overlay, lon, lat))
    if state.key in sources.POINT_SERVICES:
        out["borehole points"] = timed(lambda: f"{len(sources.borehole_points(state.key, x, y, 2000))} points in 2 km")
    if state.key in sources.LOG_SERVICES:
        out["borehole logs"] = timed(lambda: f"{len(sources.boreholes_online(state.key, x, y, 3000))} logs in 3 km")
    out["geology map"] = timed(lambda: _geology(x, y))
    survey, url, _ = sources.PORTALS[state.key]
    out["portal link"] = timed(lambda: link(url))
    return state.key, out


def check_global():
    g = {}
    g["Nominatim search"] = timed(lambda: f"{len(lookup.geocode('Marienplatz 1, München'))} hits")
    g["Nominatim reverse"] = timed(lambda: lookup.state_at(9.18, 48.77).key)
    q = "[out:json][timeout:10];way[building](48.775,9.18,48.776,9.181);out ids;"
    for url in lookup.OVERPASS:
        g["Overpass " + url.split("/")[2]] = timed(
            lambda url=url: f"{len(lookup._get(url, {'data': q}, timeout=25).json().get('elements', []))} buildings")
    tile = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/17/45000/68700"
    g["Esri World Imagery"] = timed(lambda: link(tile))
    return g


def main():
    with ThreadPoolExecutor(8) as pool:
        states = dict(pool.map(lambda s: _safe(check_state, s), STATES))
    result = {"global": check_global(), "states": states}
    lines = ["| State | Source | Status | Detail | s |", "|---|---|---|---|---|"]
    for name, r in result["global"].items():
        lines.append(f"| all | {name} | {'OK' if r['ok'] else 'FAIL'} | {r['detail']} | {r['s']} |")
    for key, checks in states.items():
        for name, r in checks.items():
            if name == "name":
                continue
            lines.append(f"| {key} | {name} | {'OK' if r['ok'] else 'FAIL'} | {str(r['detail']).replace('|', '/')} | {r['s']} |")
    table = "\n".join(lines)
    print(table)
    Path("source_status.md").write_text(table + "\n")
    Path("source_status.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))


def _safe(fn, state):
    try:
        return fn(state)
    except Exception:  # noqa: BLE001
        return state.key, {"name": state.name, "check": {"ok": False, "detail": traceback.format_exc()[-300:], "s": 0}}


if __name__ == "__main__":
    main()
