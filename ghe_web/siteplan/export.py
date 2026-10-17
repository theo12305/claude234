"""Files for a site plan: the borehole shapefile, a full GIS project and a preview map."""
from __future__ import annotations

import datetime as dt
import html
import io
import zipfile

import matplotlib
import matplotlib.pyplot as plt
import shapefile  # pyshp
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from pyproj import CRS
from pyproj.enums import WktVersion

from .layout import Rules, Site, allowed_area
from .lookup import EPSG, to_wgs84

matplotlib.use("Agg")

PRJ = CRS.from_epsg(EPSG).to_wkt(WktVersion.WKT1_ESRI)


def _polygons(geom) -> list:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in getattr(geom, "geoms", []) for g in _polygons(g)]


def _shp_points(stem: str, points, spacing: float) -> dict[str, bytes]:
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POINT) as w:
        for name, kind, size, dec in (("ID", "N", 6, 0), ("X", "N", 12, 2), ("Y", "N", 12, 2),
                                      ("LON", "N", 12, 7), ("LAT", "N", 12, 7), ("SPACING", "N", 6, 2)):
            w.field(name, kind, size=size, decimal=dec)
        for i, (x, y) in enumerate(points, start=1):
            lon, lat = to_wgs84(x, y)
            w.point(x, y)
            w.record(i, x, y, lon, lat, spacing)
    return {f"{stem}.shp": shp.getvalue(), f"{stem}.shx": shx.getvalue(), f"{stem}.dbf": dbf.getvalue(),
            f"{stem}.prj": PRJ.encode(), f"{stem}.cpg": b"UTF-8"}


def _shp_polygons(stem: str, rows: list[tuple[object, dict]]) -> dict[str, bytes]:
    """``rows`` are (geometry, attributes); every geometry may be a polygon or multipolygon."""
    shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
    with shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POLYGON) as w:
        w.field("ID", "N", size=6)
        w.field("NAME", "C", size=80)
        w.field("AREA_M2", "N", size=14, decimal=1)
        for i, (geom, attrs) in enumerate(rows, start=1):
            rings = []
            for poly in _polygons(geom):
                # shapefile convention: outer rings clockwise, holes counter-clockwise
                rings.append(list(poly.exterior.coords)[::-1] if poly.exterior.is_ccw else list(poly.exterior.coords))
                for hole in poly.interiors:
                    rings.append(list(hole.coords) if hole.is_ccw else list(hole.coords)[::-1])
            if not rings:
                continue
            w.poly(rings)
            w.record(i, str(attrs.get("name", ""))[:80], round(geom.area, 1))
    return {f"{stem}.shp": shp.getvalue(), f"{stem}.shx": shx.getvalue(), f"{stem}.dbf": dbf.getvalue(),
            f"{stem}.prj": PRJ.encode(), f"{stem}.cpg": b"UTF-8"}


def _zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def borehole_zip(points, spacing: float) -> bytes:
    """One point shapefile (UTM 32N, EPSG:25832), zipped; the sizing step reads it directly."""
    return _zip(_shp_points("bhe_positions", points, spacing))


def preview_png(site: Site, rules: Rules, points, title: str = "", dpi: int = 150) -> bytes:
    """Site plan: parcel, buildings with their distance, allowed area and numbered boreholes."""
    fig, ax = plt.subplots(figsize=(8.3, 7.4))
    allowed = allowed_area(site, rules)

    def draw(geom, **kw):
        for poly in _polygons(geom):
            verts, codes = [], []
            for ring in [poly.exterior, *poly.interiors]:
                c = list(ring.coords)
                verts += c
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), **kw))
            kw.pop("label", None)

    draw(site.parcel, facecolor="#f4f1e8", edgecolor="#5b4a2f", lw=1.6, label="Parcel")
    draw(allowed, facecolor="#cfe8d4", edgecolor="#3c8a4f", lw=0.8, ls="--", label="Allowed area")
    for i, b in enumerate(site.buildings):
        draw(b, facecolor="#9a9a9a", edgecolor="#555555", lw=0.8, label="Building" if i == 0 else None)
    for i, e in enumerate(site.exclusions):
        draw(e, facecolor="#f2c4c4", edgecolor="#b44", lw=0.8, hatch="//", label="Excluded area" if i == 0 else None)
    if points:
        xs, ys = zip(*points)
        ax.scatter(xs, ys, s=22, color="#1f5fbf", zorder=5, label=f"Borehole ({len(points)})")
        if len(points) <= 150:
            for i, (x, y) in enumerate(points, start=1):
                ax.annotate(str(i), (x, y), xytext=(3, 3), textcoords="offset points", fontsize=6, color="#1f3f7f")
    minx, miny, maxx, maxy = site.parcel.bounds
    pad = max(maxx - minx, maxy - miny) * 0.06 + 2
    ax.set_xlim(minx - pad, maxx + pad)
    ax.set_ylim(miny - pad, maxy + pad)
    ax.set_aspect("equal")
    ax.ticklabel_format(useOffset=False, style="plain")
    ax.tick_params(labelsize=7)
    ax.set_xlabel("Easting [m] (ETRS89 / UTM 32N)", fontsize=8)
    ax.set_ylabel("Northing [m]", fontsize=8)
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)
    ax.set_title(title or "Borehole site plan", fontsize=11, loc="left")
    ax.text(1.01, 0.0, f"Distances: parcel border {rules.border_distance:g} m, buildings "
            f"{rules.building_distance:g} m,\nboreholes {rules.spacing:g} m apart", transform=ax.transAxes,
            fontsize=7, va="bottom")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _qgis_project(layers: list[tuple[str, str, str]], imagery: tuple[str, str] | None) -> bytes:
    """A small QGIS project that opens the shapefiles (and the aerial image as a WMS layer) in one click.
    ``layers`` are (file, layer name, geometry type), drawn in list order on top of each other."""
    crs = f"""<spatialrefsys><authid>EPSG:{EPSG}</authid></spatialrefsys>"""
    maplayers, tree = [], []
    for k, (path, name, geom) in enumerate(layers):
        lid = f"layer_{k}"
        maplayers.append(f"""<maplayer type="vector" geometry="{geom}"><id>{lid}</id>
<datasource>./{path}</datasource><layername>{html.escape(name)}</layername><srs>{crs}</srs>
<provider encoding="UTF-8">ogr</provider></maplayer>""")
        tree.append(f'<layer-tree-layer id="{lid}" name="{html.escape(name)}" checked="Qt::Checked" '
                    f'source="./{path}" providerKey="ogr" expanded="1"/>')
    if imagery:
        url, layer = imagery
        src = html.escape(f"contextualWMSLegend=0&crs=EPSG:{EPSG}&dpiMode=7&format=image/png&layers={layer}"
                          f"&styles&url={url}")
        maplayers.append(f"""<maplayer type="raster"><id>imagery</id><datasource>{src}</datasource>
<layername>Aerial image (DOP)</layername><srs>{crs}</srs><provider>wms</provider></maplayer>""")
        tree.append(f'<layer-tree-layer id="imagery" name="Aerial image (DOP)" checked="Qt::Checked" '
                    f'source="{src}" providerKey="wms" expanded="0"/>')
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis projectname="BHE site plan" version="3.34.0">
<title>BHE site plan</title>
<projectCrs>{crs}</projectCrs>
<layer-tree-group>
{chr(10).join(tree)}
</layer-tree-group>
<projectlayers>
{chr(10).join(maplayers)}
</projectlayers>
</qgis>
""".encode()


def project_zip(site: Site, rules: Rules, points, info: dict[str, str], imagery: tuple[str, str] | None = None) -> bytes:
    """Everything for a GIS program: shapefiles of boreholes, parcel, buildings, exclusions and allowed area,
    the preview map, a QGIS project and a short read-me."""
    allowed = allowed_area(site, rules)
    files: dict[str, bytes] = {}
    files.update(_shp_points("bhe_positions", points, rules.spacing))
    files.update(_shp_polygons("parcel", [(site.parcel, {"name": info.get("Parcel", "")})]))
    files.update(_shp_polygons("allowed_area", [(allowed, {"name": "allowed borehole area"})]))
    layers = [("allowed_area.shp", "Allowed area", "Polygon"), ("parcel.shp", "Parcel", "Polygon")]
    if site.buildings:
        files.update(_shp_polygons("buildings", [(b, {"name": "building"}) for b in site.buildings]))
        layers.append(("buildings.shp", "Buildings", "Polygon"))
    if site.exclusions:
        files.update(_shp_polygons("exclusions", [(e, {"name": "excluded"}) for e in site.exclusions]))
        layers.append(("exclusions.shp", "Excluded areas", "Polygon"))
    layers.append(("bhe_positions.shp", "Borehole positions", "Point"))
    files["site_plan.png"] = preview_png(site, rules, points, info.get("Parcel", ""))
    # QGIS draws the first layer of the tree on top, so reverse: boreholes on top, image at the bottom
    files["site_plan.qgs"] = _qgis_project(layers[::-1], imagery)
    lines = [f"BHE site plan, created {dt.date.today():%Y-%m-%d} with GHEtool Web", ""]
    lines += [f"{k}: {v}" for k, v in info.items()]
    lines += ["", f"Boreholes: {len(points)}", f"Distance to parcel border: {rules.border_distance:g} m",
              f"Distance to buildings: {rules.building_distance:g} m",
              f"Distance between boreholes: {rules.spacing:g} m",
              f"Allowed area: {allowed.area:,.0f} m2", "",
              f"Coordinates: ETRS89 / UTM zone 32N (EPSG:{EPSG}).",
              "Open site_plan.qgs in QGIS, or load the .shp files in any GIS program.",
              "bhe_positions.shp can be uploaded directly under Borefield > Irregular field (shapefile).", "",
              "Check the distances with the local water authority (Untere Wasserbehoerde) before planning:",
              "rules differ by state and district, and the parcel and building data may be out of date."]
    files["README.txt"] = "\n".join(lines).encode("utf-8")
    return _zip(files)
