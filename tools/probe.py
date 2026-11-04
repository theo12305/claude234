"""Temporary: probe candidate service addresses (status, layer names, links)."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests

UA = {"User-Agent": "GHEtool-Web site plan (https://github.com/theo12305/claude234)"}
BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def get(url, params=None, headers=UA, timeout=60):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout, allow_redirects=True)
        return r
    except Exception as exc:  # noqa: BLE001
        print(f"  ERR {type(exc).__name__}: {str(exc)[:150]}")
        return None


def caps(url, service, version):
    print(f"\n== {service} {url}")
    r = get(url, {"SERVICE": service, "REQUEST": "GetCapabilities", "VERSION": version})
    if r is None:
        return
    print(f"  {r.status_code} {r.headers.get('Content-Type')} {r.url[:120]}")
    tag = "Name" if service == "WMS" else "Name"
    if service == "WFS":
        names = re.findall(r"<(?:\w+:)?FeatureType[^>]*>\s*<(?:\w+:)?Name[^>]*>([^<]+)<", r.text)
    else:
        names = re.findall(r"<(?:\w+:)?Layer[^>]*>\s*<(?:\w+:)?Name>([^<]+)<", r.text)
    print("  names:", names[:40])
    if not names:
        print("  body:", re.sub(r"\s+", " ", r.text[:400]))


def page(url, pattern="", headers=UA):
    print(f"\n== PAGE {url}")
    r = get(url, headers=headers, timeout=30)
    if r is None:
        return
    print(f"  {r.status_code} -> {r.url[:150]}")
    if pattern:
        links = sorted(set(re.findall(r'href="([^"]*(?:' + pattern + r')[^"]*)"', r.text, re.I)))
        print("  links:", links[:30])


def raw(url, params=None, n=300):
    print(f"\n== RAW {url} {params}")
    r = get(url, params)
    if r is not None:
        print(f"  {r.status_code} {r.headers.get('Content-Type')} {len(r.content)} B")
        print("  ", re.sub(r"\s+", " ", r.text[:n]))


if __name__ == "__main__":
    exec(open(sys.argv[1]).read())
