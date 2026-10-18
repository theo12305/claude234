"""The ground layers panel in step ①: predict the layers at the site, edit them, use them.

Streamlit code only; the method is in predict.py, the data in sources.py and rocks.py.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from .. import plots
from ..siteplan import lookup
from ..siteplan.lookup import LookupError_
from . import predict, rocks, sources

SITE_PLAN = "siteplan."  # session state prefix of the site plan step


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=64)
def _surface(x: float, y: float) -> list[dict]:
    return sources.surface_geology(x, y)


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=32)
def _online_logs(state_key: str | None, x: float, y: float, radius: float) -> list[predict.Borehole]:
    return sources.boreholes_online(state_key, x, y, radius)


@st.cache_data(ttl=24 * 3600, show_spinner=False, max_entries=64)
def _state_at(x: float, y: float) -> str | None:
    state = lookup.state_at(*lookup.to_wgs84(x, y))
    return state.key if state else None


def _site_from_plan() -> tuple[float, float, str, str | None] | None:
    parcel = st.session_state.get(SITE_PLAN + "parcel")
    if parcel is None:
        return None
    c = parcel.centroid
    return c.x, c.y, st.session_state.get(SITE_PLAN + "parcel_label", "Parcel"), st.session_state.get(SITE_PLAN + "state")


def _location(key: str):
    """The site as (x, y, label, state key or None) in UTM 32N, from the site plan or an address."""
    plan = _site_from_plan()
    options = (["The parcel from the site plan"] if plan else []) + ["An address", "Coordinates"]
    how = st.radio("Location", options, horizontal=True, key=f"{key}.how",
                   help="Where the boreholes will be. Find your parcel in step ⓪ Site plan to use it here.")
    if how == "The parcel from the site plan":
        st.caption(f"📍 {plan[2]}")
        return plan
    if how == "An address":
        c1, c2 = st.columns([4, 1], vertical_alignment="bottom")
        query = c1.text_input("Address", key=f"{key}.address", placeholder="e.g. Hauptstraße 5, 52062 Aachen")
        if c2.button("Find", key=f"{key}.find", width="stretch", icon=":material/travel_explore:") and query.strip():
            try:
                hits = lookup.geocode(query.strip())
            except LookupError_ as exc:
                st.error(str(exc), icon=":material/error:")
                hits = None
            if hits:
                x, y = lookup.to_utm(hits[0]["lon"], hits[0]["lat"])
                st.session_state[f"{key}.site"] = (x, y, hits[0]["label"], None)
            elif hits == []:
                st.warning("No address found.", icon=":material/warning:")
        site = st.session_state.get(f"{key}.site")
        if site:
            st.caption(f"📍 {site[2]}")
        return site
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude [°]", 47.0, 55.2, 50.94, 0.001, format="%.5f", key=f"{key}.lat")
    lon = c2.number_input("Longitude [°]", 5.8, 15.1, 6.96, 0.001, format="%.5f", key=f"{key}.lon")
    x, y = lookup.to_utm(lon, lat)
    return x, y, f"{lat:.5f} N, {lon:.5f} E", None


def _uploaded_logs(key: str, site) -> tuple[list[predict.Borehole], list[str]]:
    up_col, tpl_col = st.columns([3, 1])
    files = up_col.file_uploader(
        "Borehole logs you have (optional): BoreholeML (.xml) from a state portal, or a table (.csv, .xlsx) with "
        "one row per layer", type=["xml", "bml", "csv", "txt", "xlsx"], accept_multiple_files=True,
        key=f"{key}.logs")
    tpl_col.download_button("Table template", sources.template_csv(), "borehole_logs_template.csv", "text/csv",
                            icon=":material/download:", key=f"{key}.tpl",
                            help="Columns: borehole, x, y (or lon, lat), top, bottom, description (words or "
                                 "SEP 3 code such as 'mS,g' or 'Tst'), groundwater. Rows without coordinates "
                                 "are a log on the site itself.")
    if not files:
        return [], []
    crs = st.selectbox("Coordinate system of the table", list(sources.EPSG_CHOICES), key=f"{key}.crs")
    holes, notes = [], []
    for f in files:
        try:
            if f.name.lower().endswith((".xml", ".bml")):
                found = sources.parse_bml(f.getvalue(), f"upload ({f.name})")
                if not found:
                    notes.append(f"{f.name}: no boreholes with layers.")
                holes += found
            else:
                found, more = sources.read_table(f.name, f.getvalue(), sources.EPSG_CHOICES[crs],
                                                 (site[0], site[1]) if site else None)
                holes += found
                notes += more
        except (LookupError_, sources.TableError) as exc:
            st.error(f"{f.name}: {exc}", icon=":material/error:")
    if holes:
        st.caption(f"Read {len(holes)} borehole log(s) from your files.")
    return holes, notes


def _predict_panel(key: str, depth_default: float) -> None:
    site = _location(key)
    uploaded, upload_notes = _uploaded_logs(key, site)
    c1, c2, c3, c4 = st.columns(4)
    radius = c1.number_input("Search radius [m]", 50.0, 10000.0, 1000.0, 50.0, key=f"{key}.radius",
                             help="Logs further away are not used. Nearer logs weigh more (1 / distance²).")
    max_n = int(c2.number_input("Most boreholes used", 1, 30, 8, 1, key=f"{key}.max_n"))
    depth = c3.number_input("Predict down to [m]", 10.0, 1000.0, float(depth_default), 10.0, key=f"{key}.depth",
                            help="At least the deepest borehole you consider; the last layer continues below.")
    gw = c4.number_input("Groundwater depth [m]", 0.0, 200.0, None, 0.5, key=f"{key}.gw", placeholder="from logs",
                         help="Loose sediments above the groundwater table conduct heat worse (VDI 4640). Empty: "
                              "from the logs, if they have it, else all layers count as water saturated.")
    c5, c6 = st.columns([2, 1])
    online = c5.toggle("Ask the open data services (BGR geological map of Germany; borehole logs of GD NRW)",
                       value=True, key=f"{key}.online")
    bedrock = c6.selectbox("Rock below the logs", ["Continue the deepest layer"] + rocks.NAMES[:-1],
                           key=f"{key}.bedrock")
    if not st.button("Predict the layers", type="primary", icon=":material/layers:", key=f"{key}.go",
                     disabled=site is None and not uploaded):
        if site is None and not uploaded:
            st.caption("Choose a location (or upload logs) first.")
        return
    if site is None:  # only uploaded logs: predict at the nearest log
        site = (uploaded[0].x, uploaded[0].y, uploaded[0].name, None)
    x, y, label, state_key = site
    holes, notes, units = list(uploaded), list(upload_notes), []
    if online:
        with st.spinner("Asking the geological services..."):
            try:
                units = _surface(x, y)
            except LookupError_ as exc:
                notes.append(f"Geological map: {exc}")
            state_unknown = False
            try:
                state_key = state_key or _state_at(x, y)
            except LookupError_:
                state_key, state_unknown = None, True
            if state_unknown:
                notes.append("Could not find out the state of this location (the address service did not "
                             "answer), so no borehole database was asked.")
            elif state_key in sources.LOG_SERVICES:
                try:
                    found = _online_logs(state_key, x, y, radius)
                    holes += found
                    notes.append(f"{sources.LOG_SERVICES[state_key]}: {len(found)} logged borehole(s) within "
                                 f"{radius:,.0f} m.")
                except LookupError_ as exc:
                    notes.append(f"Borehole logs: {exc}")
            else:
                notes.append("No open service with borehole logs is connected for this state yet. Most state "
                             "surveys show logs in their map portals (often as BoreholeML download): upload them "
                             "above to use them.")
    surface_rock = next((u["rock"] for u in units if u["rock"] != rocks.UNKNOWN), None)
    result = predict.predict(holes, x, y, depth, radius, max_n, groundwater=gw, surface_rock=surface_rock,
                             bedrock=None if bedrock.startswith("Continue") else bedrock)
    result.notes = notes + result.notes
    st.session_state[f"{key}.prediction"] = (result, units, label, gw)


def _show_prediction(key: str, prefix: str, length: float, buried: float) -> None:
    saved = st.session_state.get(f"{key}.prediction")
    if not saved:
        return
    result, units, label, gw = saved
    st.markdown(f"**Predicted layers at {label}**")
    for note in result.notes:
        st.caption(note)
    left, right = st.columns([3, 2])
    with left:
        table = pd.DataFrame([{"From [m]": l.top, "To [m]": l.bottom, "Rock": l.rock, "k [W/(m·K)]": l.k_s,
                               "C [MJ/(m³·K)]": l.c, "Confidence": l.confidence, "Basis": l.basis}
                              for l in result.layers])
        st.dataframe(table, hide_index=True, width="stretch", column_config={
            "Confidence": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1)})
        k, c = predict.effective(result.rows(), length, buried)
        st.metric("Average over the borehole", f"{k:.2f} W/(m·K)", f"{c:.2f} MJ/(m³·K), {length:.0f} m borehole",
                  delta_color="off", delta_arrow="off")
        b1, b2 = st.columns(2)
        b1.button("Fill in the averages", key=f"{key}.apply_avg", icon=":material/input:", width="stretch",
                  on_click=_apply, args=(key, prefix, result.rows(), k, c, False),
                  help="Puts the average conductivity and heat capacity into the fields above.")
        b2.button("Use the layers", key=f"{key}.apply_layers", type="primary", icon=":material/layers:",
                  width="stretch", on_click=_apply, args=(key, prefix, result.rows(), k, c, True),
                  help="Copies the layers into the layer table and calculates with them (and fills in the "
                       "averages too).")
        if units:
            st.caption("Geological map (BGR GÜK250) at the site: " + "; ".join(
                f"{u['material']} ({u['age']}){', cover' if u['cover'] else ''}" for u in units))
        if result.used:
            st.dataframe(pd.DataFrame([{"Borehole": b.name, "Distance [m]": round(d), "Weight": w,
                                        "Depth [m]": b.depth, "Source": b.source} for b, d, w in result.used]),
                         hide_index=True, width="stretch", column_config={
                             "Weight": st.column_config.ProgressColumn(format="percent", min_value=0, max_value=1)})
    with right:
        fig = plots.borehole_log(result.rows(), length, buried, "Predicted layers", groundwater=gw)
        st.pyplot(fig, width="stretch")


def _apply(key: str, prefix: str, rows: list[dict], k: float, c: float, use: bool) -> None:
    st.session_state[f"{prefix}.k_s"] = round(float(k), 2)
    st.session_state[f"{prefix}.volumetric_heat_capacity"] = round(float(c), 2)
    if use:
        st.session_state[f"{key}.rows"] = [dict(r) for r in rows]
        st.session_state[f"{key}.ver"] = st.session_state.get(f"{key}.ver", 0) + 1
        st.session_state[f"{key}.use"] = True


def _clear(key: str) -> None:
    st.session_state[f"{key}.rows"] = []
    st.session_state[f"{key}.ver"] = st.session_state.get(f"{key}.ver", 0) + 1
    st.session_state[f"{key}.use"] = False


def _editor(key: str, rows: list[dict]) -> list[dict]:
    """The editable layer table. Picking another rock fills in its values."""
    df = pd.DataFrame([{"To depth [m]": float(r["bottom"]), "Rock": r.get("rock") or rocks.UNKNOWN,
                        "k [W/(m·K)]": float(r["k_s"]), "C [MJ/(m³·K)]": float(r["C"])} for r in rows],
                      columns=["To depth [m]", "Rock", "k [W/(m·K)]", "C [MJ/(m³·K)]"])
    df.index = range(1, len(df) + 1)
    ver = st.session_state.get(f"{key}.ver", 0)
    edited = st.data_editor(df, num_rows="dynamic", width="stretch", key=f"{key}.table.{ver}", column_config={
        "To depth [m]": st.column_config.NumberColumn(min_value=0.1, step=0.5, required=True,
                                                      help="Bottom of the layer. The last layer continues "
                                                           "downwards."),
        "Rock": st.column_config.SelectboxColumn(options=rocks.NAMES, required=True,
                                                 help="Choosing a rock fills in its VDI 4640 values."),
        "k [W/(m·K)]": st.column_config.NumberColumn(min_value=0.1, max_value=10.0, step=0.1, format="%.2f"),
        "C [MJ/(m³·K)]": st.column_config.NumberColumn(min_value=0.5, max_value=5.0, step=0.1, format="%.2f"),
    })
    # rows whose rock was just changed (and not their k) take the new rock's values
    edits = (st.session_state.get(f"{key}.table.{ver}") or {}).get("edited_rows", {})
    new_rock = {int(i) for i, cells in edits.items() if "Rock" in cells and "k [W/(m·K)]" not in cells}
    entries = []
    for i, row in enumerate(edited.itertuples(index=False)):
        bottom, rock, k, c = row
        if bottom is None or bottom != bottom:
            continue
        if i in new_rock:
            k, c = None, None
        entries.append((float(bottom), rock or rocks.UNKNOWN, k, c))
    new_rows = predict.rows_from_table(entries)
    for new, old in zip(new_rows, rows):  # keep where a layer came from while it is unchanged
        if (new["rock"], new["bottom"]) == (old.get("rock"), float(old["bottom"])) and old.get("basis"):
            new["basis"], new["confidence"] = old["basis"], old.get("confidence")
    if new_rock:  # redraw so the table shows the new rock's values
        st.session_state[f"{key}.rows"] = new_rows
        st.session_state[f"{key}.ver"] = ver + 1
        st.rerun()
    return new_rows


def layers_input(prop, value: dict, key: str, prefix: str, length: float, buried: float) -> dict:
    """The panel. ``prefix`` is the widget key prefix of the ground section (for filling in k and C)."""
    if f"{key}.rows" not in st.session_state:
        st.session_state[f"{key}.rows"] = [dict(r) for r in value.get("rows") or ()]
    if f"{key}.use" not in st.session_state:
        st.session_state[f"{key}.use"] = bool(value.get("use"))
    rows = st.session_state[f"{key}.rows"]
    st.markdown("**Ground layers**")
    use = st.toggle("Calculate with the layers (layered ground)", key=f"{key}.use",
                    help="Each layer keeps its own conductivity and heat capacity; GHEtool averages them over the "
                         "borehole length while it sizes, so a deeper borehole reaches other layers. Off: the single "
                         "values above are used.")
    with st.expander("🔮 Predict the layers from nearby borehole logs and the geological map", expanded=not rows):
        st.caption("Looks for logged boreholes around the site and interpolates their layers (nearer logs weigh "
                   "more), then gives every layer its VDI 4640 conductivity and heat capacity. It is a first "
                   "estimate for planning; a thermal response test measures the real value.")
        _predict_panel(key, max(100.0, round((length + buried) * 1.5 / 10) * 10))
        _show_prediction(key, prefix, length, buried)
    if rows or use:
        st.caption("Layer table: edit the depths and rocks, add or delete rows. Tops follow from the row above.")
        rows = _editor(key, rows)  # the session keeps the table's starting rows; the editor keeps the edits
        if rows:
            k, c = predict.effective(rows, length, buried)
            st.caption(f"Average over the {length:.0f} m borehole: k = {k:.2f} W/(m·K), C = {c:.2f} MJ/(m³·K)."
                       + ("" if use else " Switch on the layered calculation above to use the layers."))
        st.button("Clear the layers", key=f"{key}.clear", icon=":material/delete:", on_click=_clear, args=(key,))
    return {"use": bool(use), "rows": tuple(dict(r) for r in rows)}
