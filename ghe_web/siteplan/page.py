"""The "Site plan" step: find a parcel, check buildings on the aerial image, place boreholes, export.

Streamlit code only; the geometry is in layout.py, the data services in lookup.py and states.py.
"""
from __future__ import annotations

import json

import folium
import shapely
import streamlit as st
from folium.plugins import Draw
from shapely.geometry import Point, shape
from streamlit_folium import st_folium

from .. import i18n
from ..i18n import fmt, t
from . import export, lookup
from .layout import Rules, Site, allowed_area, check, place_boreholes
from .states import STATES, by_key

K = "siteplan."  # session state prefix
HOW = {"address": "Address", "number": "Flurstück number", "click": "Click on the map", "draw": "Draw the outline",
       "upload": "Upload outline"}
ESRI = ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Esri World Imagery (Esri, Maxar, Earthstar Geographics)")


def _ss(name, default=None):
    return st.session_state.get(K + name, default)


def _set(name, value):
    st.session_state[K + name] = value


def _set_parcel(feature: lookup.Feature, state_key: str | None, label: str | None = None) -> None:
    _set("parcel", feature.geometry)
    _set("parcel_label", label or feature.attrs.get("_label", t("Parcel")))
    _set("state", state_key)
    for name in ("buildings", "building_note", "points", "drawn", "ignored", "result_key"):
        st.session_state.pop(K + name, None)
    _set("map_gen", _ss("map_gen", 0) + 1)


def _state_options():
    """State keys for the drop-down; "" means: detect it from the location."""
    return [""] + [s.key for s in STATES]


def _state_name(key: str) -> str:
    return by_key(key).name if key else t("Detect from the location")


@st.cache_data(ttl=3600, show_spinner=False, max_entries=50)
def _geocode(query: str):
    return lookup.geocode(query)


@st.cache_data(ttl=3600, show_spinner=False, max_entries=200)
def _state_at(lon: float, lat: float) -> str | None:
    state = lookup.state_at(lon, lat)
    return state.key if state else None


# ---------------------------------------------------------------- 1 find the parcel

def _find_parcel(chosen_state):
    how = st.radio(t("Find the parcel by"), list(HOW), format_func=lambda k: t(HOW[k]), horizontal=True,
                   key=K + "find_by")

    def fetch_at(lon, lat):
        state = chosen_state
        if state is None:
            key = _safe_state(lon, lat)
            state = by_key(key) if key else None
        if state is None:
            st.error(t("Could not tell which state this is. Choose the Bundesland above."))
            return
        with st.spinner(t("Loading the parcel from the cadastre of {state}...", state=state.name)):
            try:
                feat, state = lookup.parcel_at(lon, lat, state)
            except lookup.LookupError_ as exc:
                st.error(str(exc), icon=":material/error:")
                return
        _set_parcel(feat, state.key)
        st.rerun()

    if how == "address":
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        query = c1.text_input(t("Address"), placeholder=t("e.g. Hauptstraße 5, 52062 Aachen"), key=K + "address")
        if c2.button(t("Search"), key=K + "search", width="stretch", icon=":material/search:") and query.strip():
            try:
                _set("hits", _geocode(query.strip()))
            except lookup.LookupError_ as exc:
                st.error(str(exc))
        hits = _ss("hits") or []
        if hits:
            labels = [h["label"] for h in hits]
            pick = st.selectbox(t("Matching places"), labels, key=K + "hit")
            hit = hits[labels.index(pick)]
            if st.button(t("Load the parcel at this address"), type="primary", key=K + "load_addr",
                         icon=":material/download:"):
                fetch_at(hit["lon"], hit["lat"])
        elif _ss("hits") == []:
            st.warning(t("No address found. Try without the house number, or click the parcel on the map."))
        st.caption(t("The address search uses OpenStreetMap. The parcel under the address point is loaded; if it is "
                     "the wrong one (e.g. the street), click the right parcel on the map instead."))

    elif how == "number":
        state = chosen_state
        if state is None:
            st.info(t("Choose the Bundesland above to search by Flurstück number."), icon=":material/info:")
            return
        c = st.columns(4)
        gem = c[0].text_input(t("Gemarkung number"), key=K + "gem",
                              help=t("4 digits, e.g. 3412. It is on the Liegenschaftskarte or in the Grundbuch "
                                     "(Gemarkungsschlüssel), not the Gemarkung name."))
        flur = c[1].text_input(t("Flur"), key=K + "flur", help=t("Leave empty in states without Flur (e.g. Bayern)."))
        zae = c[2].text_input(t("Flurstück (Zähler)"), key=K + "zae",
                              help=t("The number before the slash, e.g. 123 in 123/4."))
        nen = c[3].text_input(t("Nenner (optional)"), key=K + "nen",
                              help=t("The number after the slash, e.g. 4 in 123/4."))
        if st.button(t("Search the Flurstück"), type="primary", key=K + "load_no", icon=":material/search:"):
            with st.spinner(t("Searching the cadastre of {state}...", state=state.name)):
                try:
                    feats = lookup.parcel_by_number(state, gem, flur, zae, nen)
                except lookup.LookupError_ as exc:
                    st.error(str(exc), icon=":material/error:")
                    return
            if not feats:
                st.error(t("No Flurstück with this number was found. Check the Gemarkung number, or use the address "
                           "or the map."), icon=":material/error:")
            elif len(feats) > 1:
                _set("candidates", feats)
            else:
                _set_parcel(feats[0], state.key)
                st.rerun()
        cands = _ss("candidates") or []
        if cands:
            labels = [fmt("{label} ({area:,.0f} m²)", label=f.attrs.get("_label"), area=f.geometry.area) for f in cands]
            pick = st.selectbox(t("Several parcels match"), labels, key=K + "cand")
            if st.button(t("Use this parcel"), key=K + "use_cand"):
                _set_parcel(cands[labels.index(pick)], state.key)
                st.session_state.pop(K + "candidates", None)
                st.rerun()

    elif how in ("click", "draw"):
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        jump = c1.text_input(t("Go to an address"), placeholder=t("e.g. Hauptstraße 5, 52062 Aachen"), key=K + "jump")
        if c2.button(t("Go"), key=K + "go", width="stretch", icon=":material/travel_explore:") and jump.strip():
            try:
                hits = _geocode(jump.strip())
            except lookup.LookupError_ as exc:
                st.error(str(exc))
                hits = None
            if hits:
                _set("view_centre", (hits[0]["lat"], hits[0]["lon"]))
                _set("view_zoom", 18)
            elif hits == []:
                st.warning(t("Address not found."))
        drawing = how == "draw"
        st.caption(t("Draw the parcel with the polygon tool (left of the map), following the parcel lines. In "
                     "Bayern, choose the Bundesland above to see the parcel lines of the cadastre map.")
                   if drawing else t("Zoom in on the aerial image and click inside your parcel."))
        centre = _ss("view_centre", (51.16, 10.45))
        m = folium.Map(location=centre, zoom_start=_ss("view_zoom", 6), max_zoom=21, tiles=None)
        _base_layers(m, chosen_state)
        if drawing:
            Draw(export=False, position="topleft",
                 draw_options={"polyline": False, "circlemarker": False, "marker": False, "circle": False},
                 edit_options={"edit": False}).add_to(m)
        folium.LayerControl(collapsed=True).add_to(m)
        out = st_folium(m, key=K + f"pickmap.{centre}", height=480, use_container_width=True,
                        returned_objects=["all_drawings"] if drawing else ["last_clicked"]) or {}
        if drawing:
            polys = _drawn_shapes(out.get("all_drawings"))
            if polys and st.button(t("Use the drawn outline"), type="primary", key=K + "use_drawn",
                                   icon=":material/check:"):
                geom = shapely.union_all(polys)
                lon, lat = lookup.to_wgs84(*geom.centroid.coords[0])
                key = chosen_state.key if chosen_state else _safe_state(lon, lat)
                _set_parcel(lookup.Feature(geom, {}), key, t("Drawn parcel"))
                st.rerun()
        else:
            click = out.get("last_clicked")
            if click:
                st.write(t("Clicked at {lat:.6f} N, {lon:.6f} E", lat=click["lat"], lon=click["lng"]))
                if st.button(t("Load the parcel at this point"), type="primary", key=K + "load_click",
                             icon=":material/download:"):
                    _set("view_centre", (click["lat"], click["lng"]))
                    _set("view_zoom", 18)
                    fetch_at(click["lng"], click["lat"])

    else:
        file = st.file_uploader(t("Parcel outline as GeoJSON, KML or zipped shapefile (any coordinate system with a "
                                  ".prj; GeoJSON and KML in degrees)"), type=["geojson", "json", "kml", "zip"],
                                key=K + "outline")
        if file is not None and st.button(t("Use this outline"), type="primary", key=K + "use_upload"):
            try:
                polys = lookup.read_polygons(file.name, file.getvalue())
            except Exception as exc:  # noqa: BLE001 (any broken file: tell the user)
                st.error(t("Could not read this file: {error}", error=exc))
                return
            if not polys:
                st.error(t("The file contains no polygon."))
                return
            geom = shapely.union_all(polys)
            if not lookup.bounds_ok(geom):
                st.error(t("The outline does not lie in Germany. Check the coordinate system (.prj)."))
                return
            lon, lat = lookup.to_wgs84(*geom.centroid.coords[0])
            key = chosen_state.key if chosen_state else _safe_state(lon, lat)
            _set_parcel(lookup.Feature(geom, {}), key, file.name)
            st.rerun()


def _safe_state(lon, lat):
    """The state key at a point, or None when the reverse geocoder is not reachable."""
    try:
        return _state_at(lon, lat)
    except lookup.LookupError_:
        return None


# ---------------------------------------------------------------- map

def _base_layers(m, state) -> None:
    """Background layers; the first one added is shown. The state's own aerial image comes first when its
    address has been checked, otherwise the worldwide Esri image."""
    esri = folium.TileLayer(ESRI[0], attr=ESRI[1], name=t("Aerial image (Esri, worldwide)"), max_zoom=21,
                            max_native_zoom=19)
    dop = None
    if state is not None and state.imagery is not None:
        dop = folium.raster_layers.WmsTileLayer(
            url=state.imagery.url, layers=state.imagery.layer, fmt=state.imagery.format, transparent=False,
            name=t("Aerial image {state} (DOP)", state=state.name), attr=state.imagery.attribution, max_zoom=21,
            overlay=False, control=True, version=state.imagery.version)
    for layer in ((dop, esri) if dop is not None and state.imagery.checked else (esri, dop)):
        if layer is not None:
            layer.add_to(m)
    folium.TileLayer("OpenStreetMap", name=t("Street map"), max_zoom=21, max_native_zoom=19).add_to(m)
    if state is not None and state.overlay is not None:
        folium.raster_layers.WmsTileLayer(
            url=state.overlay.url, layers=state.overlay.layer, fmt="image/png", transparent=True,
            name=t("Parcel boundaries (cadastre map)"), attr=state.overlay.attribution, max_zoom=21,
            overlay=True, control=True, version=state.overlay.version).add_to(m)


def _geojson(geom):
    return json.loads(shapely.to_geojson(lookup.geom_to_wgs84(geom)))


def _site_map(state, parcel, buildings, ignored, drawn, allowed, points):
    lon, lat = lookup.to_wgs84(*parcel.centroid.coords[0])
    m = folium.Map(location=(lat, lon), zoom_start=19, max_zoom=21, tiles=None)
    _base_layers(m, state)
    minx, miny, maxx, maxy = parcel.bounds
    (w, s), (e, n) = lookup.to_wgs84(minx, miny), lookup.to_wgs84(maxx, maxy)
    m.fit_bounds([(s, w), (n, e)], padding=(20, 20))
    folium.GeoJson(_geojson(allowed), name=t("Allowed area"),
                   style_function=lambda _: {"color": "#3cdc6a", "weight": 1.5, "dashArray": "5 4",
                                             "fillColor": "#3cdc6a", "fillOpacity": 0.18}).add_to(m)
    folium.GeoJson(_geojson(parcel), name=t("Parcel"),
                   style_function=lambda _: {"color": "#ffd23f", "weight": 3, "fillOpacity": 0}).add_to(m)
    fg = folium.FeatureGroup(name=t("Buildings"))
    for i, b in enumerate(buildings):
        off = i in ignored
        folium.GeoJson(_geojson(b.geometry), style_function=(lambda _, off=off: {
            "color": "#999999" if off else "#ff4b4b", "weight": 2, "dashArray": "4 4" if off else None,
            "fillColor": "#ff4b4b", "fillOpacity": 0 if off else 0.3}),
            tooltip=_building_label(i, b) + (t(" – ignored") if off else "")
        ).add_to(fg)
    fg.add_to(m)
    fd = folium.FeatureGroup(name=t("Excluded areas you drew"))
    for g in drawn:
        folium.GeoJson(_geojson(g), style_function=lambda _: {"color": "#ff8c1a", "weight": 2,
                                                             "fillColor": "#ff8c1a", "fillOpacity": 0.35}).add_to(fd)
    fd.add_to(m)
    fp = folium.FeatureGroup(name=t("Boreholes ({n})", n=len(points)))
    for i, (x, y) in enumerate(points, start=1):
        plon, plat = lookup.to_wgs84(x, y)
        folium.CircleMarker((plat, plon), radius=4, color="#ffffff", weight=1.5, fill=True, fill_color="#1f6fff",
                            fill_opacity=1, tooltip=t("BHE {n}", n=i)).add_to(fp)
    fp.add_to(m)
    Draw(export=False, position="topleft",
         draw_options={"polyline": False, "circlemarker": False, "marker": False,
                       "polygon": {"shapeOptions": {"color": "#ff8c1a"}},
                       "rectangle": {"shapeOptions": {"color": "#ff8c1a"}}, "circle": False},
         edit_options={"edit": False}).add_to(m)
    folium.LayerControl(collapsed=True).add_to(m)
    return m


def _building_label(i: int, b, area: bool = False) -> str:
    source = t(b.attrs.get("source", "cadastre"))
    if area:
        return t("Building {n} ({source}, {area:,.0f} m²)", n=i + 1, source=source, area=b.geometry.area)
    return t("Building {n} ({source})", n=i + 1, source=source)


def _drawn_shapes(features) -> list:
    """Polygons (and circles) drawn on the map, in UTM."""
    out = []
    for f in features or []:
        geom = f.get("geometry") or {}
        try:
            g = shape(geom)
        except Exception:  # noqa: BLE001 (ignore anything that is not a shape)
            continue
        if g.geom_type == "Point" and (f.get("properties") or {}).get("radius"):
            x, y = lookup.to_utm(g.x, g.y)
            out.append(Point(x, y).buffer(float(f["properties"]["radius"])))
        elif g.geom_type in ("Polygon", "MultiPolygon"):
            out.append(shapely.make_valid(lookup.geom_to_utm(g, 4326)))
    return out


# ---------------------------------------------------------------- page

def page(handoff) -> None:
    """``handoff(points)`` hands the positions (EPSG:25832) to the borefield step."""
    st.markdown(t("##### Site plan: from a Flurstück to borehole positions"))
    st.caption(t("Optional. Find your parcel, check the buildings on the aerial image, set the distances, and get "
                 "the largest number of boreholes that fit, as a shapefile for the irregular borefield."))

    with st.container(border=True):
        st.markdown(t("**1 · Parcel**"))
        keys = _state_options()
        default = keys.index(_ss("state")) if _ss("state") and by_key(_ss("state")) else 0
        picked = st.selectbox(t("Bundesland"), keys, index=default, format_func=_state_name, key=K + "state_key",
                              help=t("Detected from the address or the map point; choose it yourself if that fails."))
        chosen_state = by_key(picked) if picked else None
        _find_parcel(chosen_state)

    parcel = _ss("parcel")
    if parcel is None:
        st.info(t("Load a parcel to continue."), icon=":material/info:")
        return
    state = by_key(_ss("state")) if _ss("state") else chosen_state
    st.success(fmt("**{label}**, {state}: {area:,.0f} m²", label=_ss("parcel_label"),
                   state=state.name if state else t("state unknown"), area=parcel.area),
               icon=":material/check_circle:")

    # ------------------------------------------------ buildings
    if _ss("buildings") is None:
        official, osm, notes = [], [], []
        with st.spinner(t("Loading buildings from the cadastre and OpenStreetMap...")):
            if state is not None and state.buildings is not None:
                try:
                    official = lookup.buildings_official(state, parcel)
                    for f in official:
                        f.attrs["source"] = "cadastre"
                except lookup.LookupError_ as exc:
                    notes.append(t("Cadastre buildings: {error}", error=exc))
            elif state is not None:
                notes.append(t("{state} has no open building service; buildings come from OpenStreetMap only.",
                               state=state.name))
            try:
                osm = lookup.buildings_osm(parcel)
            except lookup.LookupError_ as exc:
                notes.append(str(exc))
        merged = lookup.merge_buildings(official, osm)
        # only what can matter: buildings within the building distance of the parcel (max 20 m)
        near = parcel.buffer(20)
        _set("buildings", [b for b in merged if b.geometry.intersects(near)])
        _set("building_note", (len(official), len([b for b in merged if b.attrs.get("source") == "OpenStreetMap"]), notes))
    buildings = _ss("buildings")
    n_off, n_osm, notes = _ss("building_note")
    for note in notes:
        st.warning(note, icon=":material/warning:")

    with st.container(border=True):
        st.markdown(t("**2 · Distances**"))
        c = st.columns(4)
        border_default = state.border_distance if state else 3.0
        rules = Rules(
            border_distance=c[0].number_input(
                t("Distance to the parcel border [m]"), 0.0, 50.0, float(border_default), 0.5,
                key=K + f"border.{state.key if state else ''}",
                help=(t(state.border_note) if state else t("No state known; 3 m is common."))
                + " " + t("Check with the Untere Wasserbehörde: districts may ask for more.")),
            building_distance=c[1].number_input(t("Distance to buildings [m]"), 0.0, 30.0, 2.0, 0.5, key=K + "bld"),
            spacing=c[2].number_input(t("Distance between boreholes [m]"), 3.0, 30.0, 6.0, 0.5, key=K + "spacing",
                                      help=t("VDI 4640 recommends at least 5 m (6 m for longer boreholes); 5 to 8 m "
                                             "is common. Closer boreholes influence each other more.")),
            exclusion_distance=c[3].number_input(t("Distance to areas you draw [m]"), 0.0, 30.0, 0.0, 0.5,
                                                 key=K + "excl",
                                                 help=t("Extra distance around the areas drawn on the map.")),
        )
        c = st.columns(4)
        limit = c[0].number_input(t("Maximum number of boreholes (0 = as many as fit)"), 0, 5000, 0, 1,
                                  key=K + "limit",
                                  help=t("With a limit, the boreholes kept are spread as far apart as possible."))
        effort = c[1].select_slider(t("Search effort"), ["quick", "normal", "thorough"], "normal", format_func=t,
                                    key=K + "effort",
                                    help=t("How many grid rotations and shifts are tried for the largest count."))

    with st.container(border=True):
        st.markdown(t("**3 · Check the buildings and mark areas to keep free**"))
        st.caption(t("Buildings: {official} from the official cadastre (red), {osm} more from OpenStreetMap. Compare "
                     "them with the aerial image: draw missing buildings, sheds, trees, pipes or a driveway with the "
                     "polygon or rectangle tool (left of the map); they are kept free. Remove buildings that no "
                     "longer exist from the list below the map.", official=n_off, osm=n_osm))
        ignored = set(_ss("ignored", set()))
        drawn = list(_ss("drawn", []))
        site = Site(parcel, [b.geometry for i, b in enumerate(buildings) if i not in ignored], drawn)
        allowed = allowed_area(site, rules)
        result_key = (parcel.wkb, tuple(sorted(ignored)), tuple(g.wkb for g in drawn), rules.border_distance,
                      rules.building_distance, rules.spacing, rules.exclusion_distance, limit, effort)
        if _ss("result_key") != result_key:
            with st.spinner(t("Placing boreholes...")):
                placed = place_boreholes(allowed, rules.spacing, limit or None,
                                         {"quick": 1, "normal": 2, "thorough": 3}[effort] if parcel.area < 200_000 else 1)
            _set("points", placed.points)
            _set("method", placed.method)
            _set("result_key", result_key)
        points = _ss("points")

        m = _site_map(state, parcel, buildings, ignored, drawn, allowed, points)
        out = st_folium(m, key=K + f"sitemap.{_ss('map_gen', 0)}", height=560, use_container_width=True,
                        returned_objects=["all_drawings"])
        new = _drawn_shapes((out or {}).get("all_drawings"))
        known = {g.wkb for g in drawn}
        added = [g for g in new if g.wkb not in known]
        if added:
            _set("drawn", drawn + added)
            _set("map_gen", _ss("map_gen", 0) + 1)  # redraw with the area shown as excluded
            st.rerun()
        c1, c2 = st.columns([3, 1])
        if buildings:
            options = list(range(len(buildings)))
            keep = c1.multiselect(t("Buildings kept free"), options, [i for i in options if i not in ignored],
                                  format_func=lambda i: _building_label(i, buildings[i], area=True),
                                  key=K + f"keep_ids.{_ss('map_gen', 0)}")
            new_ignored = {i for i in options if i not in keep}
            if new_ignored != ignored:
                _set("ignored", new_ignored)
                st.rerun()
        if drawn and c2.button(t("Remove the {n} drawn area(s)", n=len(drawn)), key=K + "clear", width="stretch"):
            _set("drawn", [])
            _set("map_gen", _ss("map_gen", 0) + 1)
            st.rerun()

    with st.container(border=True):
        st.markdown(t("**4 · Result**"))
        c = st.columns(4)
        c[0].metric(t("Boreholes"), len(points))
        c[1].metric(t("Parcel"), fmt("{a:,.0f} m²", a=parcel.area))
        c[2].metric(t("Allowed area"), fmt("{a:,.0f} m²", a=allowed.area))
        c[3].metric(t("Pattern"), _pattern(_ss("method", "")))
        if not points:
            st.error(t("No borehole fits with these distances."), icon=":material/error:")
            return
        for msg in check(points, site, rules):
            st.warning(msg)
        info = {"Parcel": _ss("parcel_label"), "State": state.name if state else t("unknown")}
        imagery = (state.imagery.url, state.imagery.layer) if state and state.imagery else None
        stem = "".join(ch if ch.isalnum() else "_" for ch in _ss("parcel_label"))[:40].strip("_") or "parcel"
        c = st.columns(4)
        c[0].download_button(t("BHE shapefile (.zip)"), export.borehole_zip(points, rules.spacing),
                             f"bhe_positions_{stem}.zip", "application/zip", width="stretch",
                             icon=":material/download:", key=K + "dl_bhe",
                             help=t("One point per borehole, ETRS89 / UTM 32N. Can be uploaded under Borefield."))
        c[1].download_button(t("GIS project (.zip)"), _project_zip(site, rules, points, info, imagery),
                             f"site_plan_{stem}.zip", "application/zip", width="stretch",
                             icon=":material/folder_zip:", key=K + "dl_project",
                             help=t("Shapefiles of boreholes, parcel, buildings, drawn areas and allowed area, a QGIS "
                                    "project (site_plan.qgs) with the aerial image, the preview map and a read-me."))
        png = _png(site, rules, points, _ss("parcel_label"))
        c[2].download_button(t("Preview map (.png)"), png, f"site_plan_{stem}.png", "image/png", width="stretch",
                             icon=":material/image:", key=K + "dl_png")
        if c[3].button(t("Use in the sizing"), type="primary", width="stretch", icon=":material/arrow_forward:",
                       key=K + "handoff", help=t("Sets Borefield to an irregular field with these positions.")):
            handoff(points)
        with st.expander(t("Preview map")):
            st.image(png, width="stretch")


def _pattern(method: str) -> str:
    """The placement method ("hexagonal grid at 15°, 20 kept") as a short name in the current language."""
    name = method.split(",")[0]
    if not name:
        return "–"
    for kind in ("hexagonal", "square"):
        if name.startswith(kind + " grid at "):
            return t(kind + " grid at {angle}", angle=name.rsplit(" ", 1)[-1])
    return t(name)


def _project_zip(site, rules, points, info, imagery):
    return _zip_cached(site.parcel.wkb, tuple(b.wkb for b in site.buildings), tuple(d.wkb for d in site.exclusions),
                       (rules.border_distance, rules.building_distance, rules.spacing, rules.exclusion_distance),
                       tuple(points), tuple(info.items()), imagery, i18n.language())


@st.cache_data(max_entries=8, show_spinner=False)
def _zip_cached(parcel_wkb, buildings_wkb, drawn_wkb, rules_t, points_t, info_t, imagery, language):
    site = Site(shapely.from_wkb(parcel_wkb), [shapely.from_wkb(b) for b in buildings_wkb],
                [shapely.from_wkb(d) for d in drawn_wkb])
    with i18n.using(language):
        return export.project_zip(site, Rules(*rules_t), list(points_t), dict(info_t), imagery)


@st.cache_data(max_entries=8, show_spinner=False)
def _png_cached(parcel_wkb, buildings_wkb, drawn_wkb, rules_t, points_t, title, language):
    site = Site(shapely.from_wkb(parcel_wkb), [shapely.from_wkb(b) for b in buildings_wkb],
                [shapely.from_wkb(d) for d in drawn_wkb])
    with i18n.using(language):
        return export.preview_png(site, Rules(*rules_t), list(points_t), title)


def _png(site, rules, points, title):
    return _png_cached(site.parcel.wkb, tuple(b.wkb for b in site.buildings), tuple(d.wkb for d in site.exclusions),
                       (rules.border_distance, rules.building_distance, rules.spacing, rules.exclusion_distance),
                       tuple(points), title, i18n.language())
