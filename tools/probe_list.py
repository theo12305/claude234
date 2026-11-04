x, y = 390000, 5819000  # Berlin centre in UTM 32N approx (13.405, 52.52)
from pyproj import Transformer
bx, by = Transformer.from_crs(4326, 25832, always_xy=True).transform(13.4050, 52.5200)
bb = f"{bx-30},{by-30},{bx+30},{by+30},urn:ogc:def:crs:EPSG::25832"
for tn in ("alkis_flurstuecke:flurstuecke",):
    raw("https://gdi.berlin.de/services/wfs/alkis_flurstuecke",
        {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": tn, "SRSNAME": "EPSG:25832",
         "COUNT": 5, "BBOX": bb}, 600)
caps("https://gdi.berlin.de/services/wfs/alkis_flurstuecke", "WFS", "2.0.0")
caps("https://gdi.berlin.de/services/wfs/alkis_gebaeude", "WFS", "2.0.0")

hx, hy = Transformer.from_crs(4326, 25832, always_xy=True).transform(9.9937, 53.5511)
caps("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Gebaeude_2D_ALKIS", "WFS", "2.0.0")
raw("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Gebaeude_2D_ALKIS",
    {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature", "TYPENAMES": "bu-core2d:Building",
     "SRSNAME": "EPSG:25832", "COUNT": 5, "BBOX": f"{hx-60},{hy-60},{hx+60},{hy+60},urn:ogc:def:crs:EPSG::25832"}, 600)
caps("https://geodienste.hamburg.de/WFS_HH_ALKIS_vereinfacht", "WFS", "2.0.0")

for u in ("https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs",
          "https://www.geoproxy.geoportal-th.de/geoproxy/services/INSPIRE_CP_ALKIS",
          "https://www.geoproxy.geoportal-th.de/geoproxy/services/inspire_cp_alkis"):
    caps(u, "WFS", "2.0.0")

for u in ("https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-free-images.ows",
          "https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-freeimages.ows",
          "https://www.gds.hessen.de/wms/he_dop",
          "https://gds.hessen.de/wms/he_dop20"):
    caps(u, "WMS", "1.3.0")

for u in ("https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP_WMS_OpenData/guest",
          "https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP20_WMS_OpenData/guest",
          "https://www.geodatenportal.sachsen-anhalt.de/wss/service/ST_LVermGeo_DOP20_OpenData/guest",
          "https://www.geodatenportal.sachsen-anhalt.de/gateway/gateto/LVermGeo_Inspire-ST_LVermGeo_GDI_DOP20_Monitoring",
          "https://geodatenportal.sachsen-anhalt.de/wss/service/INSPIRE_LVermGeo_DOP20_WMS/guest"):
    caps(u, "WMS", "1.3.0")

page("https://lagb.sachsen-anhalt.de/service/landesbohrdatenbank/")
page("https://lagb.sachsen-anhalt.de/", "bohr")
page("https://lagb.sachsen-anhalt.de/geologie/", "bohr")
page("https://umweltportal.schleswig-holstein.de/portal/")
page("https://umweltportal.schleswig-holstein.de/", "bohr|geolog|karte")
page("https://www.schleswig-holstein.de/DE/landesregierung/themen/umwelt-naturschutz/geologie-boden/geologie/geologie_node.html", "bohr|daten")
page("https://www.saarland.de/lvgl/DE/GeoportalSaarland/geoportalsaarland_node")
page("https://www.saarland.de/lvgl/DE/GeoportalSaarland/geoportalsaarland_node", headers=BROWSER)
page("https://geoportal.saarland.de/", headers=BROWSER)
page("https://www.saarland.de/lua/DE/home/home_node.html", "geolog|bohr", headers=BROWSER)

q = "[out:json][timeout:10];way[building](48.775,9.18,48.776,9.181);out ids;"
for u in ("https://overpass-api.de/api/interpreter", "https://lz4.overpass-api.de/api/interpreter",
          "https://z.overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
          "https://overpass.private.coffee/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
          "https://overpass.openstreetmap.ru/api/interpreter"):
    raw(u, {"data": q}, 120)
