import time, math
from pyproj import Transformer
T = Transformer.from_crs(4326, 25832, always_xy=True)
T33 = Transformer.from_crs(4326, 25833, always_xy=True)

def merc(lon, lat, h=150):
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) * 20037508.34 / math.pi
    return f"{x-h},{y-h},{x+h},{y+h}"

def getmap(url, layer, lon, lat, version="1.3.0", fmt="image/png"):
    k = "CRS" if version == "1.3.0" else "SRS"
    raw(url, {"SERVICE": "WMS", "VERSION": version, "REQUEST": "GetMap", "LAYERS": layer, "STYLES": "", k: "EPSG:3857",
              "BBOX": merc(lon, lat), "WIDTH": 256, "HEIGHT": 256, "FORMAT": fmt, "TRANSPARENT": "TRUE"}, 80)

HE = "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-images.ows"
for l in ("he_dop20_rgb", "he_dop_rgb"):
    getmap(HE, l, 8.6821, 50.1109)
ST = "https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest"
getmap(ST, "lsa_lvermgeo_dop20_2", 11.6276, 52.1205)

bx, by = T33.transform(13.4050, 52.5200)
for u, tn in (("https://gdi.berlin.de/services/wfs/alkis_flurstuecke", "alkis_flurstuecke:flurstuecke"),
              ("https://gdi.berlin.de/services/wfs/alkis_gebaeude", "alkis_gebaeude:gebaeude")):
    raw(u, {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": tn, "SRSNAME": "EPSG:25833",
            "COUNT": 3, "BBOX": f"{bx-40},{by-40},{bx+40},{by+40},urn:ogc:def:crs:EPSG::25833"}, 300)

hx, hy = T.transform(9.9937, 53.5511)
bb = f"{hx-60},{hy-60},{hx+60},{hy+60}"
H = "https://geodienste.hamburg.de/HH_WFS_INSPIRE_Gebaeude_2D_ALKIS"
for b in (bb, bb + ",EPSG:25832", bb + ",urn:ogc:def:crs:EPSG::25832"):
    raw(H, {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "bu-core2d:Building",
            "SRSNAME": "urn:ogc:def:crs:EPSG::25832", "COUNT": 3, "BBOX": b}, 200)
raw("https://geodienste.hamburg.de/WFS_HH_ALKIS_vereinfacht", {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
    "TYPENAMES": "ave:GebaeudeBauwerk", "SRSNAME": "EPSG:25832", "COUNT": 3, "BBOX": bb + ",urn:ogc:def:crs:EPSG::25832"}, 300)
raw("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Flurstuecke", {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
    "TYPENAMES": "cp:CadastralParcel", "SRSNAME": "EPSG:25832", "COUNT": 3, "BBOX": bb + ",urn:ogc:def:crs:EPSG::25832"}, 200)

tx, ty = T.transform(11.0299, 50.9848)
TH = "https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs"
for v, extra in (("2.0.0", {}), ("1.1.0", {})):
    t0 = time.time()
    p = {"SERVICE": "WFS", "VERSION": v, "REQUEST": "GetFeature", "SRSNAME": "EPSG:25832"}
    if v == "2.0.0":
        p |= {"TYPENAMES": "ave:Flurstueck", "COUNT": 3, "BBOX": f"{tx-30},{ty-30},{tx+30},{ty+30},urn:ogc:def:crs:EPSG::25832"}
    else:
        p |= {"TYPENAME": "ave:Flurstueck", "MAXFEATURES": 3, "BBOX": f"{tx-30},{ty-30},{tx+30},{ty+30},EPSG:25832"}
    raw(TH, p, 200)
    print("   took", round(time.time() - t0, 1), "s")
caps("https://www.geoproxy.geoportal-th.de/geoproxy/services/INSPIREDLCP", "WFS", "2.0.0")
caps("https://www.geoproxy.geoportal-th.de/geoproxy/services/cp_alkis_dls", "WFS", "2.0.0")

page("https://www.geodaten.lagb.sachsen-anhalt.de/", "bohr|karte|map")
page("https://lagb.sachsen-anhalt.de/", "bohr", headers=BROWSER)
page("https://umweltportal.schleswig-holstein.de/kartendienste", "geolog|bohr")
page("https://www.schleswig-holstein.de/DE/landesregierung/themen/umwelt-naturschutz/geologie/geologie_node.html", "bohr|daten|umweltportal")
page("https://geoportal.saarland.de/", "geolog|bohr")
