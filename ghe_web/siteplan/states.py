"""Open data services and border distance rules of the 16 German states.

Edit this file when a state moves a service: every entry is plain data. ``parcels`` / ``buildings`` are
WFS layers (None where the state publishes no open data), ``imagery`` is the aerial image (DOP) WMS shown
as the map background in the browser.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Wfs:
    url: str
    typename: str
    version: str = "2.0.0"
    epsg: int = 25832
    ref_property: str | None = None  # attribute holding the Flurstückskennzeichen, for the search by number
    extra_params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Wms:
    url: str
    layer: str
    attribution: str
    format: str = "image/png"
    version: str = "1.3.0"
    checked: bool = True  # False: address taken from documentation only, so the Esri image is shown first


@dataclass(frozen=True)
class State:
    key: str            # ISO 3166-2 code without "DE-"
    code: str           # Länderschlüssel, first two digits of the Flurstückskennzeichen
    name: str
    parcels: Wfs | None
    buildings: Wfs | None
    imagery: Wms | None
    border_distance: float  # m, borehole to the parcel border
    border_note: str
    overlay: Wms | None = None  # parcel boundaries as an image, where there is no open parcel WFS


CP = "cp:CadastralParcel"
BU = "bu-core2d:Building"
CP_REF = "cp:nationalCadastralReference"
AVE_REF = "ave:flstkennz"
VDI = "VDI 4640 Blatt 2 is commonly cited with 3 m to the border; LAWA recommends 5 m."

STATES: list[State] = [
    State("SH", "01", "Schleswig-Holstein",
          Wfs("https://service.gdi-sh.de/SH_INSPIREDOWNLOAD_AI_CP_ALKIS", CP, ref_property=CP_REF),
          Wfs("https://service.gdi-sh.de/SH_INSPIREDOWNLOAD_AIII_BU", BU),
          Wms("https://service.gdi-sh.de/WMS_SH_DOP20col_OpenGBD", "sh_dop20_rgb", "© GeoBasis-DE/LVermGeo SH, CC BY 4.0"),
          6.0, "Leitfaden Schleswig-Holstein: 6 m to the border (5 m for probes shallower than 50 m); "
               "a revised Leitfaden is in preparation."),
    State("HH", "02", "Hamburg",
          Wfs("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Flurstuecke", CP, ref_property=CP_REF),
          Wfs("https://geodienste.hamburg.de/HH_WFS_INSPIRE_Gebaeude_2D_ALKIS", BU),
          Wms("https://geodienste.hamburg.de/wms_dop_zeitreihe_belaubt", "dop_zeitreihe_belaubt",
              "© Freie und Hansestadt Hamburg, LGV, dl-de/by-2.0"),
          5.0, "Leitfaden Erdwärmenutzung Hamburg 2021, section 5.7: 5 m to the border."),
    State("NI", "03", "Niedersachsen",
          Wfs("https://www.inspire.niedersachsen.de/doorman/noauth/alkis-dls-cp", CP, ref_property=CP_REF),
          Wfs("https://www.inspire.niedersachsen.de/doorman/noauth/alkis-dls-bu-core2d", BU),
          Wms("https://opendata.lgln.niedersachsen.de/doorman/noauth/dop_wms", "ni_dop20", "© LGLN, CC BY 4.0"),
          5.0, "LBEG GeoBerichte 24 (Niedersachsen): 5 m to the border; less only with the neighbour's consent."),
    State("HB", "04", "Bremen",
          Wfs("https://geodienste.bremen.de/wfs_hduk2958loah3976niun", "app:flurstuecke", ref_property="flstkennz"),
          Wfs("https://opendata.lgln.niedersachsen.de/doorman/noauth/alkishb_wfs_sf", "adv:AX_Gebaeude"),
          Wms("https://geodienste.bremen.de/wms_dop_lb", "dop10_2025_HB,dop10_2025_BHV", "© GeoInformation Bremen, CC BY 4.0"),
          5.0, "Bremen publishes no fixed value (set in the permit); 5 m is the conservative LAWA value. " + VDI),
    State("NW", "05", "Nordrhein-Westfalen",
          Wfs("https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-flurstuecke_alkis", CP, ref_property=CP_REF),
          Wfs("https://www.wfs.nrw.de/geobasis/wfs_nw_inspire-gebaeude-2d_alkis", BU),
          Wms("https://www.wms.nrw.de/geobasis/wms_nw_dop", "nw_dop_rgb", "© Geobasis NRW, dl-de/zero-2.0"),
          3.0, "LANUV-Arbeitsblatt 39 (2024), section 3.1.5: 3 m to the border."),
    State("HE", "06", "Hessen",
          Wfs("https://inspire-hessen.de/ows/services/org.2.07247d95-adc7-4c7d-9c7a-ed17af855317_wfs", CP,
              ref_property=CP_REF),
          Wfs("https://inspire-hessen.de/ows/services/org.2.1f07430b-f7b0-4c4e-a698-fb6c60384f59_wfs", BU),
          Wms("https://www.gds-srv.hessen.de/cgi-bin/lika-services/ogc-freeimages.ows", "he_dop_rgb",
              "© HVBG, dl-de/zero-2.0", checked=False),
          5.0, "HLNUG Leitfaden Erdwärmenutzung, 6th edition 2019: 5 m to the border (up to 30 kW)."),
    State("RP", "07", "Rheinland-Pfalz",
          Wfs("https://geo5.service24.rlp.de/wfs/alkis_rp.fcgi", "ave:Flurstueck", ref_property=AVE_REF),
          Wfs("https://geo5.service24.rlp.de/wfs/alkis_rp.fcgi", "ave:GebaeudeBauwerk"),
          Wms("https://geo4.service24.rlp.de/wms/rp_dop20.fcgi", "rp_dop20", "© GeoBasis-DE/LVermGeoRP, dl-de/by-2.0"),
          3.0, "SGD Nord Leitfaden Erdwärmesonden 2017 and LGB Mindestanforderungen 2024: 3 m to the border."),
    State("BW", "08", "Baden-Württemberg",
          Wfs("https://owsproxy.lgl-bw.de/owsproxy/wfs/WFS_INSP_BW_Flst_ALKIS", CP, ref_property=CP_REF),
          Wfs("https://owsproxy.lgl-bw.de/owsproxy/wfs/WFS_INSP_BW_Gebaeude_ALKIS", BU),
          Wms("https://owsproxy.lgl-bw.de/owsproxy/ows/WMS_LGL-BW_ATKIS_DOP_20_C", "IMAGES_DOP_20_RGB",
              "© LGL-BW, dl-de/by-2.0"),
          3.0, "LQS EWS Baden-Württemberg 2018, section 2.1.3: half the borehole spacing of VDI 4640, "
               "typically 3 m."),
    State("BY", "09", "Bayern", None, None,
          Wms("https://geoservices.bayern.de/od/wms/dop/v1/dop20", "by_dop20c", "© Bayerische Vermessungsverwaltung, CC BY 4.0"),
          3.0, "LfU Merkblatt 3.7/2 (Bayern): 3 m recommended (LAWA: 5 m).",
          overlay=Wms("https://geoservices.bayern.de/od/wms/alkis/v1/parzellarkarte", "by_alkis_parzellarkarte_umr_gelb",
                      "© Bayerische Vermessungsverwaltung, CC BY 4.0")),
    State("SL", "10", "Saarland",
          Wfs("https://geoportal.saarland.de/gdi-sl/inspirewfs_Flurstuecke_Grundstuecke_ALKIS", CP, epsg=4326,
              ref_property=CP_REF),
          None,
          Wms("https://geoportal.saarland.de/freewms/dop2023", "sl_dop20_rgb", "© LVGL Saarland, dl-de/by-2.0"),
          5.0, "No published value found for the Saarland; 5 m is the conservative LAWA value. " + VDI),
    State("BE", "11", "Berlin",
          Wfs("https://gdi.berlin.de/services/wfs/alkis_flurstuecke", "alkis_flurstuecke:flurstuecke",
              ref_property="fsko"),
          Wfs("https://gdi.berlin.de/services/wfs/alkis_gebaeude", "alkis_gebaeude:gebaeude"),
          Wms("https://isk.geobasis-bb.de/mapproxy/dop20c/service/wms", "bebb_dop20c", "© GeoBasis-DE/LGB, dl-de/by-2.0"),
          5.0, "The Berlin Merkblatt (2025) names no border value (10 m to neighbouring systems, 2 m to buildings); "
               "the earlier Leitfaden asked for 5 m."),
    State("BB", "12", "Brandenburg",
          Wfs("https://inspire.brandenburg.de/services/cp_alkis_wfs", CP, ref_property=CP_REF),
          Wfs("https://inspire.brandenburg.de/services/bu_alkis_wfs", BU),
          Wms("https://isk.geobasis-bb.de/mapproxy/dop20c/service/wms", "bebb_dop20c", "© GeoBasis-DE/LGB, dl-de/by-2.0"),
          3.0, "Handlungsempfehlung Erdwärmenutzung in Brandenburg (2023, updated 2025): 3 m to the border."),
    State("MV", "13", "Mecklenburg-Vorpommern",
          Wfs("https://www.geodaten-mv.de/dienste/inspire_cp_alkis_download", CP, ref_property=CP_REF),
          Wfs("https://www.geodaten-mv.de/dienste/inspire_bu_core2d_alkis_download", BU),
          Wms("https://www.geodaten-mv.de/dienste/adv_dop", "mv_dop", "© GeoBasis-DE/M-V, CC BY 4.0", checked=False),
          5.0, "Leitfaden Mecklenburg-Vorpommern (2006): 5 m to the border."),
    State("SN", "14", "Sachsen",
          Wfs("https://geodienste.sachsen.de/aaa/public_inspire/alkis/cp/dls/wfs", CP, ref_property=CP_REF),
          Wfs("https://geodienste.sachsen.de/aaa/public_alkis/vereinf/wfs", "ave:GebaeudeBauwerk"),
          Wms("https://geodienste.sachsen.de/wms_geosn_dop-rgb/guest", "sn_dop_020", "© GeoSN, dl-de/by-2.0"),
          5.0, "Sachsen: 5 m to the border is a condition for a permit-free probe (e.g. Umweltamt Dresden 2024)."),
    State("ST", "15", "Sachsen-Anhalt",
          Wfs("https://geodatenportal.sachsen-anhalt.de/ows_INSPIRE_LVermGeo_ALKIS_CP_WFS", CP, ref_property=CP_REF),
          Wfs("https://geodatenportal.sachsen-anhalt.de/ows_INSPIRE_LVermGeo_ALKIS_BU_WFS", BU),
          Wms("https://www.geodatenportal.sachsen-anhalt.de/gateway/gateto/LVermGeo_Inspire-ST_LVermGeo_GDI_DOP20_Monitoring",
              "lsa_lvermgeo_dop20", "© GeoBasis-DE/LVermGeo ST, dl-de/by-2.0", checked=False),
          5.0, "LQS Bohrungen/Erdwärmesonden Sachsen-Anhalt 2016, section 2.1.3: 5 m to the border."),
    State("TH", "16", "Thüringen",
          Wfs("https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs", "ave:Flurstueck",
              ref_property=AVE_REF),
          Wfs("https://www.geoproxy.geoportal-th.de/geoproxy/services/adv_alkis_wfs", "ave:GebaeudeBauwerk"),
          Wms("https://www.geoproxy.geoportal-th.de/geoproxy/services/DOP", "th_dop", "© GDI-Th, CC BY 4.0"),
          5.0, "Leitfaden Thüringen (2007): 5 m to the border."),
]


def by_key(key: str | None) -> State | None:
    return next((s for s in STATES if s.key == key), None)
