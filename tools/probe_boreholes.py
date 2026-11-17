"""Temporary: checks the automatic log reading against the live services and records the answers for local
screenshots (the development container cannot reach the state servers). Not part of the app."""
import gzip, pickle, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests

RECORD = {}
_orig = requests.Session.get

def recording_get(self, url, params=None, **kw):
    r = _orig(self, url, params=params, **kw)
    key = requests.Request("GET", url, params=params).prepare().url
    RECORD[key] = (r.status_code, dict(r.headers), r.content)
    return r

requests.Session.get = recording_get

from ghe_web.siteplan import lookup  # noqa: E402
from ghe_web.strata import reader, sources  # noqa: E402

SITES = {"NW": (50.94, 6.96), "BE": (52.5040, 13.3780), "SH": (54.3216, 10.1355)}

def main():
    for k, (lat, lon) in SITES.items():
        x, y = lookup.to_utm(lon, lat)
        t0 = time.time()
        try:
            print(k, "geology", [u["material"] for u in sources.surface_geology(x, y)])
        except Exception as e: print(k, "geology fail", e)
        try:
            print(k, "state", lookup.state_at(*lookup.to_wgs84(x, y)).key)
        except Exception as e: print(k, "state fail", e)
        if k in sources.LOG_SERVICES:
            try:
                holes = sources.boreholes_online(k, x, y, 1000.0)
                print(k, f"BML logs {len(holes)} in {time.time()-t0:.1f}s", [(h.name, len(h.layers)) for h in holes[:8]])
            except Exception as e: print(k, "BML fail", e)
        if k in sources.POINT_SERVICES:
            pts = sources.borehole_points(k, x, y, 1000.0)
            print(k, "points", len(pts), "readable", sum(1 for p in pts if p.log))
            readable = [p for p in pts if p.log]
            deep = [p for p in readable if (p.depth or 0) >= 10]
            for p in (deep if len(deep) >= 6 else readable)[:6]:
                t1 = time.time()
                try:
                    h = reader.read_service_log(*p.log, p.name, p.x, p.y, "test", p.depth)
                    print(f"  {p.name} ({p.depth} m) OK {time.time()-t1:.1f}s:",
                          [(l.bottom, l.rock, l.text[:40]) for l in h.layers])
                except Exception as e:
                    print(f"  {p.name} ({p.depth} m) FAIL {e}")
    Path("tools/recorded.pkl.gz").write_bytes(gzip.compress(pickle.dumps(RECORD)))
    print("recorded", len(RECORD), "answers", Path("tools/recorded.pkl.gz").stat().st_size, "bytes")

if __name__ == "__main__":
    try: main()
    except Exception: traceback.print_exc()
