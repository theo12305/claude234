"""📊 Results > Material list: the plan of the horizontal piping (click the building entrance, the manifold, draw
trenches) and the material list of the sized field."""
from __future__ import annotations

import math

import altair as alt
import pandas as pd
import streamlit as st

from .. import export, ui
from ..i18n import fmt, t
from ..results.common import figure, in_language
from ..results.registry import Ctx, ResultView, plugin_data, register
from . import network, quantities as q

KEY = "materials"
TOOLS = {"entrance": "Building entrance", "manifold": "Manifold", "trench": "Draw trench"}
COLOURS = {"bhe": "#13294b", "trench": "#0e7490", "header": "#c2410c", "draft": "#f59e0b", "entrance": "#c2410c",
           "manifold": "#0e7490", "site": "#94a3b8"}


def _state() -> dict:
    data = plugin_data(KEY)
    for k, v in q.settings(data).items():
        data.setdefault(k, v)
    return data


def _background(ctx: Ctx):
    """Parcel and buildings of the site plan in the borefield's coordinates, when the field came from the site plan
    in this session."""
    origin = st.session_state.get("site_plan_origin")
    bf = ctx.sized_inputs["borefield"]
    if not origin or bf.variant != "custom" or tuple(map(tuple, origin[1])) != tuple(map(tuple, bf.values["points"])):
        return []
    from ..siteplan import page as siteplan_page
    x0, y0 = origin[0]
    rows = []
    for i, (kind, geom) in enumerate(siteplan_page.background()):
        polys = getattr(geom, "geoms", [geom])
        for j, poly in enumerate(polys):
            ring = getattr(poly, "exterior", None)
            if ring is None:
                continue
            for k, (x, y) in enumerate(ring.coords):
                rows.append({"x": x - x0, "y": y - y0, "o": k, "id": f"{i}.{j}", "kind": t(kind)})
    return rows


def _extent(points, pad: float):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad


def plan_chart(lay: q.Layout, data: dict, background: list[dict], width: int) -> tuple[alt.LayerChart, float]:
    """The plan in metres with equal scales, and a transparent grid that turns a click into a position."""
    pts = list(lay.bhes) + [lay.entrance, lay.manifold] + [tuple(p) for line in data["trenches"] for p in line]
    pts += [tuple(p) for p in data.get("current", [])]
    x0, x1, y0, y1 = _extent(pts, 8.0)
    if background:
        bx0, bx1, by0, by1 = _extent([(r["x"], r["y"]) for r in background], 2.0)
        x0, x1, y0, y1 = min(x0, bx0), max(x1, bx1), min(y0, by0), max(y1, by1)
    span = max(x1 - x0, y1 - y0)
    step = max(0.5, math.ceil(math.sqrt((x1 - x0) * (y1 - y0) / 3500) * 2) / 2)
    ppm = width / max(x1 - x0, 1.0)
    height = int(min(max((y1 - y0) * ppm, 220), 900))
    ppm = min(ppm, height / max(y1 - y0, 1.0))
    width_px = int((x1 - x0) * ppm)
    xs = alt.Scale(domain=[x0, x1], nice=False, zero=False)
    ys = alt.Scale(domain=[y0, y1], nice=False, zero=False)
    X = lambda f="x": alt.X(f"{f}:Q", scale=xs, title="x [m]")  # noqa: E731
    Y = lambda f="y": alt.Y(f"{f}:Q", scale=ys, title="y [m]")  # noqa: E731
    layers = []
    if background:
        layers.append(alt.Chart(pd.DataFrame(background)).mark_line(color=COLOURS["site"], strokeWidth=1.2)
                      .encode(X(), Y(), order="o:Q", detail="id:N", tooltip=[alt.Tooltip("kind:N", title="")]))
    r = lay.routing
    if r.trenches:
        tr = pd.DataFrame([{"x": a[0], "y": a[1], "x2": b[0], "y2": b[1], "n": c,
                            "len": round(network._dist(a, b), 1)} for a, b, c in r.trenches])
        layers.append(alt.Chart(tr).mark_rule(color=COLOURS["trench"], opacity=0.85).encode(
            X(), Y(), x2="x2:Q", y2="y2:Q",
            strokeWidth=alt.StrokeWidth("n:Q", scale=alt.Scale(range=[1.5, 7]), legend=None),
            tooltip=[alt.Tooltip("n:Q", title=t("Circuits in the trench")),
                     alt.Tooltip("len:Q", title=t("Length [m]"))]))
    if len(r.header) > 1:
        hd = pd.DataFrame([{"x": p[0], "y": p[1], "o": i} for i, p in enumerate(r.header)])
        layers.append(alt.Chart(hd).mark_line(color=COLOURS["header"], strokeWidth=4, strokeDash=[8, 3])
                      .encode(X(), Y(), order="o:Q", tooltip=alt.value(t("Header pipe"))))
    current = data.get("current", [])
    if current:
        dr = pd.DataFrame([{"x": p[0], "y": p[1], "o": i} for i, p in enumerate(current)])
        layers.append(alt.Chart(dr).mark_line(color=COLOURS["draft"], strokeWidth=3, strokeDash=[4, 3],
                                              point=alt.OverlayMarkDef(color=COLOURS["draft"], size=40))
                      .encode(X(), Y(), order="o:Q"))
    bh = pd.DataFrame([{"x": p[0], "y": p[1], "no": i + 1} for i, p in enumerate(lay.bhes)])
    layers.append(alt.Chart(bh).mark_circle(color=COLOURS["bhe"], opacity=1,
                                            size=max(18, min(90, (3.0 * ppm) ** 2))).encode(
        X(), Y(), tooltip=[alt.Tooltip("no:Q", title=t("BHE no."))]))
    marks = [{"x": lay.entrance[0], "y": lay.entrance[1], "label": t("Building entrance") +
              (" (" + t("assumed") + ")" if lay.entrance_assumed else ""), "shape": "triangle-down",
              "c": COLOURS["entrance"], "dy": 14}]
    if not lay.manifold_in_building:
        marks.append({"x": lay.manifold[0], "y": lay.manifold[1], "label": t("Manifold"), "shape": "square",
                      "c": COLOURS["manifold"], "dy": -10})
    mk = pd.DataFrame(marks)
    layers.append(alt.Chart(mk).mark_point(filled=True, size=260, opacity=1, stroke="white", strokeWidth=1.5).encode(
        X(), Y(), shape=alt.Shape("shape:N", scale=None), color=alt.Color("c:N", scale=None),
        tooltip=alt.Tooltip("label:N", title="")))
    for dy, part in mk.groupby("dy"):  # entrance label below, manifold label above: readable when close together
        layers.append(alt.Chart(part).mark_text(align="left", dx=11, dy=int(dy), fontSize=12, fontWeight=600).encode(
            X(), Y(), text="label:N", color=alt.Color("c:N", scale=None)))
    # the click grid: invisible points, the nearest one is taken
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    grid = pd.DataFrame([{"gx": round(x0 + i * step, 2), "gy": round(y0 + j * step, 2)}
                         for i in range(nx) for j in range(ny)])
    click = alt.selection_point(name="click", fields=["gx", "gy"], nearest=True, on="click", clear=False)
    layers.append(alt.Chart(grid).mark_point(opacity=0.004, size=10).encode(
        x=alt.X("gx:Q", scale=xs, title="x [m]"), y=alt.Y("gy:Q", scale=ys, title="y [m]"),
        tooltip=alt.value(None)).add_params(click))
    chart = alt.layer(*layers).properties(width=width_px, height=height, title=t("Plan of the horizontal piping"))
    return chart, step


def _on_click(chart_key: str) -> None:
    event = st.session_state.get(chart_key) or {}
    sel = (event.get("selection") or {}).get("click") or []
    if not sel:
        return
    p = [float(sel[0]["gx"]), float(sel[0]["gy"])]
    data = plugin_data(KEY)
    tool = st.session_state.get("mat_tool", "entrance")
    if tool == "entrance":
        data["entrance"] = p
    elif tool == "manifold":
        data["manifold"], data["manifold_mode"] = p, "point"
        st.session_state[_wkey("manifold_mode", "point")] = "point"
    else:
        radius = st.session_state.get("mat_snap", 1.0)
        snapped = network.snap(tuple(p), [[tuple(x) for x in line] for line in data.get("trenches", [])],
                               [tuple(x) for x in data.get("current", [])], radius)
        data.setdefault("current", []).append(list(snapped))
    st.session_state.mat_clicks = st.session_state.get("mat_clicks", 0) + 1


def _finish_line() -> None:
    data = plugin_data(KEY)
    if len(data.get("current", [])) > 1:
        data.setdefault("trenches", []).append(data["current"])
    data["current"] = []


def _undo() -> None:
    data = plugin_data(KEY)
    if data.get("current"):
        data["current"].pop()
    elif data.get("trenches"):
        data["trenches"].pop()


def _clear() -> None:
    data = plugin_data(KEY)
    data["trenches"], data["current"] = [], []


def _wkey(name: str, value):
    """Widget key of a setting; the widget starts from the saved value (a new key after opening a project)."""
    key = f"mat.{name}.{st.session_state.get('generation', 0)}"
    if key not in st.session_state:
        st.session_state[key] = value
    return key


def _settings(data: dict, simple: bool) -> None:
    def num(col, key, label, lo, hi, step, unit, help_=""):
        data[key] = col.number_input(f"{label} [{t(unit)}]", lo, hi, step=step,
                                     key=_wkey(key, min(max(float(data[key]), lo), hi)), help=help_ or None)

    def pipe(col, key, label, help_):
        options = ["auto", *q.PE_SDR11]
        data[key] = col.selectbox(label, options, key=_wkey(key, data[key] if data[key] in options else "auto"),
                                  format_func=lambda d: t("automatic (v ≤ {v:g} m/s)", v=float(data["v_max"]))
                                  if d == "auto" else q.pipe_name(d), help=help_)

    c1, c2, c3 = st.columns(3)
    modes = list(q.MANIFOLD_MODES)
    data["manifold_mode"] = c1.selectbox(
        t("Manifold position"), modes, key=_wkey("manifold_mode", data["manifold_mode"]),
        format_func=lambda k: t(q.MANIFOLD_MODES[k]),
        help=t("Every BHE is one circuit with its own supply and return pipe to the manifold. A manifold shaft near "
               "the field needs only one pair of header pipes to the building; a manifold in the plant room needs a "
               "wall penetration for every circuit."))
    pipe(c2, "connection_pipe", t("Connection pipe (BHE to manifold)"),
         t("Automatic: the smallest PE100 SDR 11 pipe that keeps the flow velocity at the design flow per BHE below "
           "the maximum."))
    pipe(c3, "header_pipe", t("Header pipe (manifold to building)"),
         t("Automatic: the smallest PE100 SDR 11 pipe for the flow of all BHEs together within the maximum velocity."))
    more = st.expander(t("More options"), icon=":material/tune:") if simple else st.container()
    with more:
        c = st.columns(4)
        num(c[0], "trench_depth", t("Trench depth"), 0.3, 3.0, 0.1, "m",
            t("Frost-free depth for the horizontal pipes; 1.0 to 1.5 m is common."))
        num(c[1], "trench_width", t("Trench width"), 0.2, 3.0, 0.1, "m")
        num(c[2], "bedding", t("Sand bedding and cover (height)"), 0.0, 1.5, 0.05, "m",
            t("Sand under and over the pipes, e.g. 0.1 m below and 0.2 m above."))
        num(c[3], "reserve", t("Pipe reserve per circuit and line"), 0.0, 20.0, 0.5, "m",
            t("Extra pipe for each supply and return line: up from the trench at the BHE head and at the manifold."))
        c = st.columns(4)
        num(c[0], "length_step", t("BHE delivery length step"), 0.5, 50.0, 0.5, "m",
            t("BHEs are delivered in fixed lengths; the length is rounded up to the next step."))
        num(c[1], "grout_loss", t("Grout loss factor"), 0.0, 200.0, 5.0, "%",
            t("Extra grout above the annulus volume for fissures, karst or loss into the formation. 10 to 20 % in "
              "solid rock; more in karst."))
        num(c[2], "v_max", t("Maximum flow velocity (automatic pipe size)"), 0.3, 3.0, 0.1, "m/s",
            t("Higher velocity: smaller pipes, more pressure drop. 0.8 to 1.5 m/s is common."))
        st.session_state.mat_snap = c[3].number_input(f"{t('Snap distance when drawing')} [m]", 0.0, 10.0, step=0.5,
                                                      key=_wkey("snap", 1.0),
                                                      help=t("A click this close to the end or corner of a trench "
                                                             "joins it."))


def table(items: list[q.Item]) -> pd.DataFrame:
    rows = [{t("Item no."): f"{i + 1:02d}", t("Group"): it.group, t("Description"): it.description,
             t("Quantity"): round(it.quantity, it.decimals), t("Unit"): it.unit, t("Basis of quantity"): it.basis}
            for i, it in enumerate(items)]
    return pd.DataFrame(rows)


def _items(ctx: Ctx) -> tuple[q.Layout, list[q.Item]]:
    s = q.settings(plugin_data(KEY))
    lay = q.layout(ctx.result, s)
    return lay, q.material_list(ctx.result, ctx.sized_inputs, s, lay)


def render(ctx: Ctx) -> None:
    data = _state()
    ui.caption(t("Quantities from the sizing result and the horizontal piping on the plan. Click the building "
                 "entrance on the plan; the trenches are routed automatically, or draw them yourself. No prices: "
                 "export the list and price it in your own tools."))
    _settings(data, ctx.simple)
    lay, items = _items(ctx)
    bar = st.container(horizontal=True, vertical_alignment="bottom", gap="small", key="mat_toolbar")
    tool = bar.segmented_control(t("Click on the plan to set"), list(TOOLS), format_func=lambda k: t(TOOLS[k]),
                                 default="entrance", required=True, key="mat_tool")
    if tool == "trench":
        bar.button(t("Finish line"), icon=":material/check:", on_click=_finish_line,
                   disabled=len(data.get("current", [])) < 2)
        bar.button(t("Undo last point"), icon=":material/undo:", on_click=_undo,
                   disabled=not (data.get("current") or data.get("trenches")))
    if data.get("trenches") or data.get("current"):
        bar.button(t("Delete drawn trenches (automatic routing)"), icon=":material/delete:", on_click=_clear,
                   type="tertiary")
    chart, step = plan_chart(lay, data, _background(ctx), 340 if ui.is_phone() else 760)
    key = f"mat_plan.{st.session_state.get('mat_clicks', 0)}"
    st.markdown(f"<span class='fignum'>{t('Figure {n}', n=str(st.session_state.get('_view_number', 0)) + '.1')}"
                f"</span>", unsafe_allow_html=True)
    st.altair_chart(chart, on_select=lambda: _on_click(key), selection_mode="click", key=key, width="content")
    hints = {"entrance": t("Click where the header pipes enter the building."),
             "manifold": t("Click where the manifold shaft goes."),
             "trench": t("Click the corners of a trench one after the other, then Finish line. Lines that touch or "
                         "cross are joined; each BHE and the manifold are joined to the nearest trench.")}
    ui.caption(hints[tool] + " " + t("Dark blue: BHEs. Teal: trenches, thicker with more circuits. Orange dashed: "
                                     "header pipe. Click resolution {s:g} m.", s=step))
    if lay.entrance_assumed:
        st.info(t("The building entrance is assumed 10 m west of the field. Click it on the plan for the real "
                  "lengths."), icon=":material/info:")
    if lay.routing.unconnected:
        st.warning(t("{n} BHE(s) are not reached by the drawn trenches and are joined straight to the manifold: "
                     "no. {nos}.", n=len(lay.routing.unconnected),
                     nos=", ".join(str(i + 1) for i in lay.routing.unconnected)), icon=":material/warning:")
    r = lay.routing
    connection = sum(2 * (p + float(data["reserve"])) for p in r.paths)
    volume = next(it.quantity for it in items if it.group == t("Heat transfer fluid"))
    ui.tiles([("⛏️ " + t("Trench length"), fmt("{x:,.0f} m", x=r.trench_length), t("circuits and header"), ""),
              ("〰️ " + t("Connection pipe"), fmt("{x:,.0f} m", x=connection),
               t("longest circuit {x:.0f} m", x=max(r.paths) + data["reserve"]), ""),
              ("➡️ " + t("Header pipe"), fmt("{x:,.1f} m", x=r.header_length),
               t("manifold to building, single length") if not lay.manifold_in_building else t("manifold in the "
                                                                                                 "building"), ""),
              ("💧 " + t("System volume"), fmt("{x:,.2f} m³", x=volume), t("heat transfer fluid"), "")])
    df = table(items)
    st.markdown(f"<span class='fignum'>{t('Table {n}', n=str(st.session_state.get('_view_number', 0)) + '.2')}"
                f"</span><div class='figtitle'>{t('Material list')}</div>", unsafe_allow_html=True)
    shown = df.copy()  # numbers in the page's language (the downloads keep plain numbers)
    shown[t("Quantity")] = [fmt("{x:,.%df}" % it.decimals, x=it.quantity) for it in items]
    st.dataframe(shown, hide_index=True, width="stretch",
                 column_config={t("Quantity"): st.column_config.TextColumn(width="small")})
    c1, c2 = st.columns(2)
    c1.download_button(t("Material list (Excel)"), in_language(lambda: export.tables_workbook({t("Material list"): df})),
                       f"{ctx.stem}_materials.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       icon=":material/table_view:", on_click="ignore", width="stretch")
    c2.download_button(t("Material list (CSV)"), df.to_csv(index=False).encode(), f"{ctx.stem}_materials.csv",
                       "text/csv", icon=":material/download:", on_click="ignore", width="stretch")
    ui.caption(t("The material list and the plan settings are saved with the project (menu ☰ > Save project) and "
                 "are part of the Excel export under Export."))


def tables(ctx: Ctx) -> dict[str, pd.DataFrame]:
    try:
        return {t("Material list"): table(_items(ctx)[1])}
    except Exception:  # an odd borefield must not break the export
        return {}


# Hidden for now (theo, 2026-11-04: "keep it hidden, we might need it later"). To show it again, drop available=.
register(ResultView(KEY, "Material list", 850, render, tables=tables, available=lambda ctx: False))
