"""Where boreholes may go on a parcel, and as many positions as fit.

Pure geometry (shapely), in a projected coordinate system in metres (UTM, EPSG:25832).
No web or network code, so it can be tested on its own.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import shapely
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from ..i18n import t

TOL = 1e-6  # m; points exactly on the edge of the allowed area count as inside


@dataclass
class Site:
    parcel: Polygon | MultiPolygon
    buildings: list[Polygon] = field(default_factory=list)
    exclusions: list[Polygon] = field(default_factory=list)  # extra areas drawn or uploaded by the user


@dataclass
class Rules:
    border_distance: float = 3.0     # m, borehole to parcel border
    building_distance: float = 2.0   # m, borehole to buildings
    spacing: float = 6.0             # m, borehole to borehole
    exclusion_distance: float = 0.0  # m, borehole to the extra exclusion areas


def allowed_area(site: Site, rules: Rules):
    """The part of the parcel where a borehole centre may be placed."""
    area = site.parcel.buffer(-rules.border_distance, join_style="mitre") if rules.border_distance > 0 \
        else site.parcel
    blocked = [b.buffer(rules.building_distance) if rules.building_distance > 0 else b for b in site.buildings]
    blocked += [e.buffer(rules.exclusion_distance) if rules.exclusion_distance > 0 else e for e in site.exclusions]
    if blocked:
        area = area.difference(unary_union(blocked))
    return shapely.make_valid(area) if not area.is_empty else area


# ---------------------------------------------------------------- placement

class _Grid:
    """Spatial hash for "is any accepted point closer than the spacing?"."""

    def __init__(self, spacing: float):
        self.s = spacing
        self.s2 = (spacing - TOL) ** 2
        self.cells: dict[tuple[int, int], list[tuple[float, float]]] = {}
        self.points: list[tuple[float, float]] = []

    def free(self, x: float, y: float) -> bool:
        i, j = math.floor(x / self.s), math.floor(y / self.s)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for px, py in self.cells.get((i + di, j + dj), ()):
                    if (px - x) ** 2 + (py - y) ** 2 < self.s2:
                        return False
        return True

    def add(self, x: float, y: float) -> None:
        self.cells.setdefault((math.floor(x / self.s), math.floor(y / self.s)), []).append((x, y))
        self.points.append((x, y))

    def offer(self, xs, ys) -> None:
        for x, y in zip(xs, ys):
            if self.free(x, y):
                self.add(x, y)


def _inside(area, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    return shapely.contains_xy(area.buffer(TOL), xs, ys) if len(xs) else np.zeros(0, bool)


def _lattice(area, spacing: float, angle: float, ox: float, oy: float, hexagonal: bool, anchor=None):
    """Points of a square or hexagonal lattice that fall inside the area. The lattice passes through
    ``anchor`` (default: the centre of the area), shifted by ``ox``/``oy`` of a cell."""
    minx, miny, maxx, maxy = area.bounds
    cx, cy = anchor or ((minx + maxx) / 2, (miny + maxy) / 2)
    r = math.hypot(max(abs(maxx - cx), abs(minx - cx)), max(abs(maxy - cy), abs(miny - cy))) + spacing
    dy = spacing * math.sqrt(3) / 2 if hexagonal else spacing
    n_i, n_j = int(r / spacing) + 2, int(r / dy) + 2
    i, j = np.meshgrid(np.arange(-n_i, n_i + 1), np.arange(-n_j, n_j + 1))
    u = (i + (0.5 * (j % 2) if hexagonal else 0)) * spacing + ox * spacing
    v = j * dy + oy * dy
    c, s = math.cos(angle), math.sin(angle)
    xs, ys = (cx + c * u - s * v).ravel(), (cy + s * u + c * v).ravel()
    keep = _inside(area, xs, ys)
    return xs[keep], ys[keep]


def _ring_points(area, step: float):
    """Points along every edge of the area: first the corners, then evenly spaced along each ring."""
    corners, along = [], []
    polys = area.geoms if hasattr(area, "geoms") else [area]
    for poly in polys:
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        for ring in [poly.exterior, *poly.interiors]:
            coords = list(ring.coords)[:-1]
            n = len(coords)
            for k, (x, y) in enumerate(coords):
                # sharp corners first: they are the places a lattice usually misses
                ax, ay = coords[k - 1]
                bx, by = coords[(k + 1) % n]
                v1, v2 = (ax - x, ay - y), (bx - x, by - y)
                norm = math.hypot(*v1) * math.hypot(*v2)
                cos_angle = (v1[0] * v2[0] + v1[1] * v2[1]) / norm if norm else 1.0
                corners.append((cos_angle, x, y))
            length = ring.length
            if length > 0:
                for d in np.arange(0, length, step):
                    p = ring.interpolate(d)
                    along.append((p.x, p.y))
    corners.sort(reverse=True)  # sharpest (largest cosine) first
    pts = [(x, y) for _, x, y in corners] + along
    return [p[0] for p in pts], [p[1] for p in pts]


def _fill(grid: _Grid, area, spacing: float) -> None:
    """Adds every point of a fine grid that still has room, so gaps left by a pattern are used."""
    minx, miny, maxx, maxy = area.bounds
    step = spacing / 6
    xs, ys = np.meshgrid(np.arange(minx, maxx + step, step), np.arange(miny, maxy + step, step))
    xs, ys = xs.ravel(), ys.ravel()
    keep = _inside(area, xs, ys)
    grid.offer(xs[keep], ys[keep])


def _boundary_first(area, spacing: float) -> list[tuple[float, float]]:
    """Fill the area ring by ring from the outside in, like peeling an onion."""
    grid = _Grid(spacing)
    current, inset = area, spacing * math.sqrt(3) / 2
    for _ in range(10_000):
        if current.is_empty:
            break
        xs, ys = _ring_points(current, spacing / 4)
        grid.offer(xs, ys)
        current = current.buffer(-inset)
    _fill(grid, area, spacing)
    return grid.points


def _lattice_then_fill(area, spacing, angle, ox, oy, hexagonal, anchor):
    grid = _Grid(spacing)
    xs, ys = _lattice(area, spacing, angle, ox, oy, hexagonal, anchor)
    grid.offer(xs, ys)
    xs, ys = _ring_points(area, spacing / 4)
    grid.offer(xs, ys)
    _fill(grid, area, spacing)
    return grid.points


@dataclass
class Placement:
    points: list[tuple[float, float]]
    method: str


def place_boreholes(area, spacing: float, max_count: int | None = None, effort: int = 2) -> Placement:
    """As many positions as possible inside ``area`` with at least ``spacing`` between any two.

    Tries rotated and shifted hexagonal and square lattices and an outside-in fill, tops each up with
    every gap that still has room, and keeps the pattern with the most boreholes. ``effort`` (1 to 3)
    sets how many rotations and shifts are tried.
    """
    if area is None or area.is_empty or spacing <= 0:
        return Placement([], "nothing fits")
    area = shapely.make_valid(area)
    best = Placement(_boundary_first(area, spacing), "outside-in rows")
    angle_step = {1: 15, 2: 5, 3: 1}[effort]
    shifts = {1: (0.0, 0.5), 2: (0.0, 0.25, 0.5, 0.75), 3: tuple(k / 8 for k in range(8))}[effort]

    # Count plain lattice points first (fast), then top up only the best few.
    # Besides plain rotations, lattices are laid along the longest edges with a row right on the edge.
    candidates = []
    for hexagonal, period in ((True, 60), (False, 90)):
        for angle_deg in range(0, period, angle_step):
            for ox in shifts:
                for oy in shifts:
                    xs, _ = _lattice(area, spacing, math.radians(angle_deg), ox, oy, hexagonal)
                    candidates.append((len(xs), hexagonal, angle_deg, ox, oy, None))
        for angle, anchor in _long_edges(area, {1: 3, 2: 6, 3: 12}[effort]):
            for ox in shifts:
                xs, _ = _lattice(area, spacing, angle, ox, 0.0, hexagonal, anchor)
                candidates.append((len(xs), hexagonal, math.degrees(angle) % period, ox, 0.0, anchor))
    candidates.sort(key=lambda c: c[0], reverse=True)
    for _, hexagonal, angle_deg, ox, oy, anchor in candidates[:{1: 4, 2: 12, 3: 30}[effort]]:
        pts = _lattice_then_fill(area, spacing, math.radians(angle_deg), ox, oy, hexagonal, anchor)
        if len(pts) > len(best.points):
            best = Placement(pts, f"{'hexagonal' if hexagonal else 'square'} grid at {angle_deg:.0f}°")
    if max_count is not None and len(best.points) > max_count:
        best = Placement(_spread_subset(best.points, max_count), best.method + f", {max_count} kept")
    return Placement([(round(x, 2), round(y, 2)) for x, y in best.points], best.method)


def _long_edges(area, n: int):
    """Direction and start point of the ``n`` longest edges of the area."""
    edges = []
    for poly in (area.geoms if hasattr(area, "geoms") else [area]):
        if poly.geom_type != "Polygon" or poly.is_empty:
            continue
        coords = list(poly.exterior.coords)
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            edges.append((math.hypot(x2 - x1, y2 - y1), math.atan2(y2 - y1, x2 - x1), (x1, y1)))
    edges.sort(reverse=True)
    return [(angle, start) for _, angle, start in edges[:n]]


def _spread_subset(points, n: int):
    """``n`` of the points, spread out as far as possible (farthest-point sampling)."""
    pts = np.asarray(points)
    centre = pts.mean(axis=0)
    chosen = [int(np.argmax(((pts - centre) ** 2).sum(axis=1)))]
    dist = ((pts - pts[chosen[0]]) ** 2).sum(axis=1)
    while len(chosen) < n:
        k = int(np.argmax(dist))
        chosen.append(k)
        dist = np.minimum(dist, ((pts - pts[k]) ** 2).sum(axis=1))
    return [tuple(map(float, pts[k])) for k in sorted(chosen)]


def check(points, site: Site, rules: Rules) -> list[str]:
    """Plain-language problems with a set of positions (used for edited layouts and in tests)."""
    problems = []
    area = allowed_area(site, rules).buffer(0.01)
    outside = [i + 1 for i, (x, y) in enumerate(points) if not area.contains(Point(x, y))]
    if outside:
        problems.append(t("{n} borehole(s) break a distance rule: {which}", n=len(outside),
                          which=", ".join(map(str, outside[:20]))))
    g = _Grid(rules.spacing - 0.01)
    close = []
    for i, (x, y) in enumerate(points):
        if not g.free(x, y):
            close.append(i + 1)
        g.add(x, y)
    if close:
        problems.append(t("{n} borehole(s) are closer than {d:g} m to another: {which}", n=len(close),
                          d=rules.spacing, which=", ".join(map(str, close[:20]))))
    return problems


# ---------------------------------------------------------------- groundwater wells

@dataclass
class WellPlacement:
    production: list[tuple[float, float]]
    injection: list[tuple[float, float]]
    distance: float  # m, between the centres of the two groups
    along_flow: float  # m, the part of it in the flow direction
    border_downstream: float  # m, from the injection wells to the parcel border in the flow direction


def flow_vector(direction: float) -> tuple[float, float]:
    """Unit vector (east, north) of the groundwater flow, ``direction`` in degrees clockwise from north."""
    a = math.radians(direction)
    return math.sin(a), math.cos(a)


def _row(cx: float, cy: float, n: int, spacing: float, v: tuple[float, float]) -> list[tuple[float, float]]:
    return [(cx + v[0] * spacing * (i - (n - 1) / 2), cy + v[1] * spacing * (i - (n - 1) / 2)) for i in range(n)]


def place_wells(area, parcel, direction: float, n_production: int = 1, n_injection: int = 1,
                spacing: float = 15.0) -> WellPlacement | None:
    """Production wells as far upstream and injection wells as far downstream as the allowed area permits, each
    group in a row across the flow, so the injected water flows away from the production wells. None when the
    groups do not fit."""
    if area is None or area.is_empty:
        return None
    area = shapely.make_valid(area)
    u = flow_vector(direction)
    v = (-u[1], u[0])
    minx, miny, maxx, maxy = area.bounds
    step = max(0.5, math.sqrt(area.area / 4000))
    xs, ys = np.meshgrid(np.arange(minx, maxx + step, step), np.arange(miny, maxy + step, step))
    xs, ys = xs.ravel(), ys.ravel()
    inside = _inside(area, xs, ys)
    xs, ys = xs[inside], ys[inside]
    if not len(xs):
        return None

    def fitting(n):
        ok = np.ones(len(xs), bool)
        for k in range(n):
            off = spacing * (k - (n - 1) / 2)
            ok &= _inside(area, xs + v[0] * off, ys + v[1] * off)
        return np.flatnonzero(ok)

    prod, inj = fitting(n_production), fitting(n_injection)
    if not len(prod) or not len(inj):
        return None
    s = xs * u[0] + ys * u[1]  # position along the flow
    lat = xs * v[0] + ys * v[1]
    prod = prod[np.argsort(s[prod])][:60]
    inj = inj[np.argsort(-s[inj])][:60]
    best = None
    for i in prod:
        rows_p = _row(xs[i], ys[i], n_production, spacing, v)
        for j in inj:
            along = s[j] - s[i]
            if along <= 0:
                continue
            score = along - 0.5 * abs(lat[j] - lat[i])
            if best is not None and score <= best[0]:
                continue
            rows_i = _row(xs[j], ys[j], n_injection, spacing, v)
            if min(math.dist(a, b) for a in rows_p for b in rows_i) < spacing:
                continue
            best = (score, rows_p, rows_i, along, i, j)
    if best is None:
        return None
    _, rows_p, rows_i, along, i, j = best
    centre_i = (float(xs[j]), float(ys[j]))
    ray = shapely.LineString([centre_i, (centre_i[0] + u[0] * 1e5, centre_i[1] + u[1] * 1e5)])
    hit = ray.intersection(parcel.boundary)
    border = min((Point(centre_i).distance(g) for g in getattr(hit, "geoms", [hit]) if not g.is_empty),
                 default=0.0)
    r2 = lambda pts: [(round(float(x), 2), round(float(y), 2)) for x, y in pts]  # noqa: E731
    return WellPlacement(r2(rows_p), r2(rows_i), round(math.dist((xs[i], ys[i]), centre_i), 1), round(float(along), 1),
                         round(float(border), 1))
