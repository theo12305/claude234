import time
from pyproj import Transformer
T = Transformer.from_crs(4326, 25832, always_xy=True)
tx, ty = T.transform(11.0299, 50.9848)
TH = "https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs"
b = f"{tx-30:.1f},{ty-30:.1f},{tx+30:.1f},{ty+30:.1f}"
variants = [
    {"VERSION": "1.1.0", "TYPENAME": "ave:Flurstueck", "MAXFEATURES": 3, "SRSNAME": "EPSG:25832", "BBOX": b + ",EPSG:25832"},
    {"VERSION": "1.1.0", "TYPENAME": "ave:Flurstueck", "MAXFEATURES": 3, "BBOX": b},
    {"VERSION": "2.0.0", "TYPENAMES": "ave:Flurstueck", "COUNT": 3, "BBOX": b},
    {"VERSION": "2.0.0", "TYPENAMES": "ave:Flurstueck", "COUNT": 3},
    {"VERSION": "2.0.0", "TYPENAMES": "ave:Flurstueck", "COUNT": 3, "SRSNAME": "urn:ogc:def:crs:EPSG::25832", "BBOX": b + ",urn:ogc:def:crs:EPSG::25832"},
]
for v in variants:
    t0 = time.time()
    raw(TH, {"SERVICE": "WFS", "REQUEST": "GetFeature", **v}, 700)
    print("   took", round(time.time() - t0, 1), "s")
raw(TH, {"SERVICE": "WFS", "REQUEST": "DescribeFeatureType", "VERSION": "2.0.0", "TYPENAMES": "ave:Flurstueck"}, 600)
r = get(TH, {"SERVICE": "WFS", "REQUEST": "GetCapabilities", "VERSION": "2.0.0"})
import re
print(re.findall(r"<(?:\w+:)?(?:DefaultCRS|OtherCRS)>([^<]+)<", r.text)[:10])
print(re.findall(r'<ows:Operation name="GetFeature">.{0,600}', r.text, re.S)[:1])
