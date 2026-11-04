import time
from ghe_web.siteplan import lookup
from ghe_web.siteplan.states import by_key
_orig = lookup._get
def loud(url, params=None, data=None, timeout=40):
    t0 = time.time()
    try:
        r = lookup._session().get(url, params=params, timeout=90)
    except Exception as e:
        print("   EXC", type(e).__name__, round(time.time() - t0, 1), "s"); raise lookup.LookupError_("x")
    print("   ", r.status_code, round(time.time() - t0, 1), "s", r.text[:400].replace("\n", " ") if r.status_code != 200 or b"Exception" in r.content[:600] else "")
    if r.status_code != 200:
        raise lookup.LookupError_("http")
    return r
lookup._get = loud

def num(key, pat):
    s = by_key(key)
    print(f"\n== {key} {pat}")
    try:
        print("   hits:", len(lookup.wfs_by_attribute(s.parcels, s.parcels.ref_property, pat)))
    except Exception as e:
        print("   ERR", e)

num("HH", "020101???01396*")
num("HH", "020101___01396*")
num("NI", "03488004500211*")
num("HE", "06046001000013*")
lookup.NAMESPACES["ave"] = "http://repository.gdi-de.org/schemas/adv/produkt/alkis-vereinfacht/1.0"
num("TH", "16010112400134*")
num("RP", "07370101700054*")
for k, lon, lat in (("NW", 6.9603, 50.9375),):
    print("\n== NW parcel_at")
    try:
        print("   ", lookup.parcel_at(lon, lat, by_key(k))[0].attrs.get("_label"))
    except Exception as e:
        print("   ERR", e)
raw("https://geodienste.hamburg.de/wms_dop_zeitreihe_belaubt", {"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.3.0"}, 200)
caps("https://geodienste.hamburg.de/wms_dop_zeitreihe_belaubt", "WMS", "1.3.0")
caps("https://geodienste.hamburg.de/HH_WMS_DOP", "WMS", "1.3.0")
