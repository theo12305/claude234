"""Temporary probe 3. Not part of the app."""
import io, re, subprocess, sys, time, traceback, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from ghe_web.siteplan import lookup
from ghe_web.strata import sources

S = requests.Session(); S.headers["User-Agent"] = "GHEtool-web source check"
OUT = Path("probe_files"); OUT.mkdir(exist_ok=True)

def ocr(content):
    p = OUT / "tmp.img"; p.write_bytes(content)
    return subprocess.run(["tesseract", str(p), "-", "-l", "deu", "--psm", "4"], capture_output=True, text=True, timeout=90).stdout

def links(html):
    out = []
    for l in re.findall(r"""(?:href|src)\s*=\s*["']?([^"'\s>]+)""", html, flags=re.I):
        out.append(l.replace("&amp;", "&").replace("\\\\", "//").replace("\\", "/"))
    return out

def get(label, url, show_html=False, do_ocr=True):
    t0 = time.time()
    try:
        r = S.get(url, timeout=45)
    except Exception as e:
        print(f"\n### {label} FAIL {type(e).__name__}: {str(e)[:200]}"); return None
    ct = r.headers.get("Content-Type", "")
    print(f"\n### {label} [{r.status_code} {ct} {len(r.content)}B {time.time()-t0:.1f}s] {r.url[:220]}")
    if "html" in ct or "xml" in ct or "json" in ct:
        print(r.text[:3000] if show_html else re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:1500])
    elif "pdf" in ct:
        from pypdf import PdfReader
        try: print("PDF TEXT:\n", "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(r.content)).pages[:3])[:3000])
        except Exception as e: print("pdf fail", e)
    elif "image" in ct and do_ocr:
        print("OCR:\n" + ocr(r.content)[:2000])
    return r

def main():
    # raw feature properties
    for k, (lon, lat) in {"BB": (13.0645, 52.3906), "BE": (13.4050, 52.52), "SH": (10.1355, 54.3216), "SN": (13.7373, 51.0504), "NI": (9.7320, 52.3759)}.items():
        x, y = lookup.to_utm(lon, lat); svc = sources.POINT_SERVICES[k]
        try:
            r = S.get(svc.url, params=sources._point_request(svc, x, y, 1500, 2), timeout=45)
            print(f"\n### {k} raw features [{r.status_code}]\n", r.text[:2500])
        except Exception as e: print(k, "raw fail", e)
    # SH start page and its links
    for k, url in (("SH", "http://141.91.161.241/geodin/getportalpage?LAYOUT=SGD_SH_start&ObjectID1=B1627K2748BRG001&PORTAL=1"),
                   ("SN", "https://www.umwelt.sachsen.de/umwelt/infosysteme/geodin/getportalpage?LAYOUT=Aufschlussdaten_Portal&ObjectID1=0000239968BRG000&PORTAL=1")):
        r = get(f"{k} start raw", url, show_html=True)
        if r is None: continue
        base = url.split("/geodin/")[0] + "/geodin/"
        for l in links(r.text):
            if l.startswith(("css", "../", "#", "mailto")) or l.endswith(".css"): continue
            if not l.startswith("http"): l = base + l.lstrip("./")
            rr = get(f"{k} -> {l[-70:]}", l, show_html=True, do_ocr=False)
    # SN: guess layouts
    for lay in ("Schichtenverzeichnis", "Schichtdaten", "SVZ", "Schichtenverzeichnis_Portal", "Bohrprofil"):
        get(f"SN layout {lay}", f"https://www.umwelt.sachsen.de/umwelt/infosysteme/geodin/getportalpage?LAYOUT={lay}&ObjectID1=0000239968BRG000&PORTAL=1", show_html=True)
    # BE more boreholes with OCR at layout 1
    x, y = lookup.to_utm(13.35, 52.50)
    for p in sources.borehole_points("BE", x, y, 2000)[:3]:
        get(f"BE {p.name} {p.depth}", re.sub(r"LAYOUT=\d+", "LAYOUT=1", p.link))

if __name__ == "__main__":
    try: main()
    except Exception: traceback.print_exc()
