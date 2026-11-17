"""Temporary probe: what the state borehole services and their log links return. Not part of the app."""
import re, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from ghe_web.siteplan import lookup
from ghe_web.strata import sources

S = requests.Session(); S.headers["User-Agent"] = "GHEtool-web source check"
POINTS = {"NI": (9.7320, 52.3759), "NW": (6.9603, 50.9375), "HE": (8.6821, 50.1109), "BE": (13.4050, 52.52),
          "BB": (13.0645, 52.3906), "MV": (11.4148, 53.6288), "SN": (13.7373, 51.0504), "SH": (10.1355, 54.3216)}

def show(label, url, params=None, n=1500, names=False):
    t0 = time.time()
    try:
        r = S.get(url, params=params, timeout=45)
        body = r.text
        txt = body
        if names:
            found = re.findall(r"<(?:\w+:)?Name>([^<]+)</(?:\w+:)?Name>\s*<(?:\w+:)?Title>([^<]*)<", body)
            txt = " ; ".join(f"{a}={b}" for a, b in found)[:n]
        else:
            txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)
            txt = re.sub(r"<[^>]+>", " ", txt); txt = re.sub(r"\s+", " ", txt)[:n]
        print(f"\n### {label} [{r.status_code} {r.headers.get('Content-Type')} {len(r.content)}B {time.time()-t0:.1f}s] {r.url[:200]}\n{txt}")
        return r
    except Exception as e:
        print(f"\n### {label} FAIL {type(e).__name__}: {str(e)[:200]} ({time.time()-t0:.1f}s)")

def main():
    # 1 capabilities: other feature types in the point services
    for k in ("BE", "BB", "MV", "SH"):
        svc = sources.POINT_SERVICES[k]
        show(f"{k} capabilities", svc.url, {"SERVICE": "WFS", "REQUEST": "GetCapabilities"}, 2500, names=True)
    show("SN layers", "https://luis.sachsen.de/arcgis/rest/services/geologie/bohrungen/MapServer", {"f": "json"}, 2500)
    show("HE layers", "https://geodienste-umwelt.hessen.de/arcgis/rest/services/geologie/bohrdatenportal/MapServer", {"f": "json"}, 2500)
    show("HE services", "https://geodienste-umwelt.hessen.de/arcgis/rest/services/geologie", {"f": "json"}, 2500)
    show("SN services", "https://luis.sachsen.de/arcgis/rest/services/geologie", {"f": "json"}, 2500)
    # 2 NRW timing
    x, y = lookup.to_utm(*POINTS["NW"])
    for ver, r, cnt in (("2.0.0", 300, 20), ("2.0.0", 1000, 50), ("1.1.0", 500, 30)):
        p = {"SERVICE": "WFS", "VERSION": ver, "REQUEST": "GetFeature", "SRSNAME": "urn:ogc:def:crs:EPSG::25832",
             "BBOX": f"{x-r},{y-r},{x+r},{y+r},urn:ogc:def:crs:EPSG::25832"}
        p |= {"TYPENAMES": "bml:Borehole", "COUNT": cnt} if ver.startswith("2") else {"TYPENAME": "bml:Borehole", "MAXFEATURES": cnt}
        rr = show(f"NW GetFeature {ver} r={r} n={cnt}", sources.NRW_BML, p, 300)
        if rr is not None and rr.ok:
            try:
                hs = sources.parse_bml(rr.content, "GD NRW"); print("parsed logged:", len(hs), [len(h.layers) for h in hs][:10])
            except Exception as e: print("parse", e)
    show("NW capabilities", sources.NRW_BML, {"SERVICE": "WFS", "REQUEST": "GetCapabilities"}, 1500, names=True)
    # 3 the log links of the point services
    for k in ("NI", "BE", "BB", "MV", "SN", "SH"):
        x, y = lookup.to_utm(*POINTS[k])
        try:
            pts = sources.borehole_points(k, x, y, 3000)
        except Exception as e:
            print(f"\n### {k} points FAIL {e}"); continue
        print(f"\n## {k}: {len(pts)} points; with link {sum(1 for p in pts if p.link)}; deep>=30m {sum(1 for p in pts if (p.depth or 0)>=30)}")
        deep = [p for p in pts if p.link and (p.depth or 0) >= 20][:3] or [p for p in pts if p.link][:3]
        for p in deep:
            print(f"- {p.name} {p.depth} {p.link}")
            r = show(f"{k} link {p.name}", p.link, None, 1800)
            if r is not None and "html" in (r.headers.get("Content-Type") or ""):
                links = re.findall(r'(?:href|src)="([^"]+)"', r.text)
                print("links:", [l for l in links if not l.startswith("#")][:40])
    # 4 BGR borehole map of Germany
    show("BGR bpk wms", "https://services.bgr.de/wms/boden/bpk/", {"SERVICE": "WMS", "REQUEST": "GetCapabilities"}, 800, names=True)
    show("BGR services", "https://services.bgr.de/arcgis/rest/services", {"f": "json"}, 3000)

if __name__ == "__main__":
    try: main()
    except Exception: traceback.print_exc()
