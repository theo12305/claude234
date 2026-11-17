"""Temporary probe: what the log links return, with OCR of pictures. Not part of the app."""
import io, re, subprocess, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from ghe_web.siteplan import lookup
from ghe_web.strata import sources

S = requests.Session(); S.headers["User-Agent"] = "GHEtool-web source check"
OUT = Path("probe_files"); OUT.mkdir(exist_ok=True)
POINTS = {"NI": (9.7320, 52.3759), "BE": (13.4050, 52.52), "BB": (13.0645, 52.3906), "SN": (13.7373, 51.0504),
          "SH": (10.1355, 54.3216)}
N = [0]

def ocr(content):
    p = OUT / "tmp.img"; p.write_bytes(content)
    try:
        return subprocess.run(["tesseract", str(p), "-", "-l", "deu", "--psm", "4"], capture_output=True, text=True, timeout=90).stdout
    except Exception as e:
        return f"OCR FAIL {e}"

def get(label, url, ocr_it=True):
    t0 = time.time()
    try:
        r = S.get(url, timeout=45)
    except Exception as e:
        print(f"\n### {label} FAIL {type(e).__name__}: {str(e)[:200]}"); return None
    ct = r.headers.get("Content-Type", "")
    N[0] += 1
    ext = "pdf" if "pdf" in ct else "png" if "png" in ct else "jpg" if ("jpg" in ct or "jpeg" in ct) else "gif" if "gif" in ct else "html"
    (OUT / f"{N[0]:02d}_{re.sub(r'[^A-Za-z0-9]+', '_', label)[:40]}.{ext}").write_bytes(r.content)
    print(f"\n### {label} [{r.status_code} {ct} {len(r.content)}B {time.time()-t0:.1f}s] {r.url[:220]}")
    if ext == "html":
        txt = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", r.text)
        print(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", txt))[:1500])
        print("links:", re.findall(r'(?:href|src)="([^"]+)"', r.text)[:30])
    elif ext == "pdf":
        from pypdf import PdfReader
        try: print("PDF TEXT:", "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(r.content)).pages[:3])[:2500])
        except Exception as e: print("pdf fail", e)
    elif ocr_it:
        from PIL import Image
        im = Image.open(io.BytesIO(r.content)); print("image size", im.size)
        print("OCR:\n" + ocr(r.content)[:2500])
    return r

def main():
    for k in POINTS:
        x, y = lookup.to_utm(*POINTS[k])
        pts = sources.borehole_points(k, x, y, 3000)
        deep = [p for p in pts if p.link and (p.depth or 0) >= 25][:2] or [p for p in pts if p.link][:2]
        for p in deep:
            print(f"\n======== {k} {p.name} depth {p.depth} {p.link}")
            r = get(f"{k} {p.name}", p.link)
            if r is None: continue
            if k == "NI":
                bid = re.search(r"BID=([^&]+)", p.link).group(1)
                base = "https://nibis.lbeg.de/DetailseitenKartenserver/DetailSeitenBohrsaeulenGeodin/"
                get(f"NI image {bid}", base + f"Bohrungsbild.ashx?BID={bid}&Seite=1&Massstab=30&ART=BDN")
                for art in ("SVZ", "SEP", "SV"):
                    get(f"NI page ART={art}", base + f"Bohrungsseite.aspx?BID={bid}&SEITE=1&ART={art}&MASSSTAB=30", False)
            if k == "BE":
                for lay in (1, 2, 3, 4, 6):
                    get(f"BE layout {lay}", re.sub(r"LAYOUT=\d+", f"LAYOUT={lay}", p.link), lay in (1, 3))
            if k in ("SN", "SH"):
                for link in re.findall(r'(?:href|src)="([^"]+)"', r.text):
                    link = link.replace("&amp;", "&").replace("\\\\", "//").replace("\\", "/")
                    if "geodin" in link:
                        rr = get(f"{k} sub {link[-60:]}", link)
                        if rr is not None and "html" in rr.headers.get("Content-Type", ""):
                            for l2 in re.findall(r'(?:href|src)="([^"]+)"', rr.text)[:6]:
                                l2 = l2.replace("&amp;", "&").replace("\\\\", "//").replace("\\", "/")
                                if "geodin" in l2 and l2 != link:
                                    get(f"{k} subsub {l2[-50:]}", l2)

if __name__ == "__main__":
    try: main()
    except Exception: traceback.print_exc()
