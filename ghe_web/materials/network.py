"""Horizontal piping: trenches from the boreholes to the manifold and the header line from the manifold to the
building entrance. Plain geometry, no Streamlit, so it is unit-tested on its own.

Every borehole heat exchanger (BHE) gets its own supply and return pipe to the manifold (one circuit), as usual in
Germany (balancing valve and flow meter per circuit at the manifold). Pipes of several circuits share a trench.

Two ways to route:
* automatic: the shortest trench network that connects all BHEs and the manifold (minimum spanning tree);
* drawn: trench lines the user drew on the plan. Each BHE, the manifold and the entrance are joined to the nearest
  trench by a short stub, crossing lines are joined where they cross, and each circuit follows the shortest way
  along the trenches.
"""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

Point = tuple[float, float]
TOL = 0.05  # m: points closer than this are the same point


@dataclass
class Routing:
    trenches: list[tuple[Point, Point, int]]  # trench segments with the number of circuits in them
    paths: list[float]  # trench length from each BHE to the manifold, in BHE order
    header: list[Point]  # header line, manifold -> building entrance (empty when the manifold is in the building)
    unconnected: list[int] = field(default_factory=list)  # BHEs (0-based) no drawn trench reaches: joined straight

    @property
    def trench_length(self) -> float:
        """Total trench length, circuits and header together (shared trenches counted once)."""
        return sum(_dist(a, b) for a, b, _ in self.trenches) + self.header_trench_length

    @property
    def header_length(self) -> float:
        return sum(_dist(a, b) for a, b in zip(self.header, self.header[1:]))

    @property
    def header_trench_length(self) -> float:
        """Header length where it does not run in a trench of the circuits."""
        shared = {_key(a, b) for a, b, _ in self.trenches}
        return sum(_dist(a, b) for a, b in zip(self.header, self.header[1:]) if _key(a, b) not in shared)


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _key(a: Point, b: Point) -> tuple:
    ra, rb = (round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))
    return (ra, rb) if ra <= rb else (rb, ra)


def auto_manifold(bhes: list[Point], entrance: Point, offset: float = 2.0) -> Point:
    """A manifold shaft just outside the field, beside the BHE nearest to the building entrance."""
    near = min(bhes, key=lambda p: _dist(p, entrance))
    d = _dist(near, entrance)
    if d < 1e-6:
        return near
    step = min(offset, d / 2)
    return near[0] + (entrance[0] - near[0]) / d * step, near[1] + (entrance[1] - near[1]) / d * step


def assumed_entrance(bhes: list[Point], distance: float = 10.0) -> Point:
    """Where the entrance is assumed until the user clicks it: west of the field, at its middle."""
    xs, ys = [p[0] for p in bhes], [p[1] for p in bhes]
    return min(xs) - distance, (min(ys) + max(ys)) / 2


# ---------------------------------------------------------------- automatic routing

def auto_routing(bhes: list[Point], manifold: Point, entrance: Point | None) -> Routing:
    """Minimum spanning tree over the manifold and all BHEs (Prim), straight header to the entrance."""
    nodes = [manifold, *bhes]
    n = len(nodes)
    parent = [-1] * n
    best = [math.inf] * n
    best[0] = 0.0
    done = [False] * n
    for _ in range(n):
        i = min((j for j in range(n) if not done[j]), key=lambda j: best[j])
        done[i] = True
        for j in range(n):
            if not done[j]:
                d = _dist(nodes[i], nodes[j])
                if d < best[j] - 1e-9:
                    best[j], parent[j] = d, i
    count = [0] * n
    paths = []
    for b in range(1, n):
        length, j = 0.0, b
        while parent[j] != -1:
            count[j] += 1
            length += _dist(nodes[j], nodes[parent[j]])
            j = parent[j]
        paths.append(length)
    trenches = [(nodes[parent[j]], nodes[j], count[j]) for j in range(1, n) if _dist(nodes[j], nodes[parent[j]]) > TOL]
    header = [manifold, entrance] if entrance is not None and _dist(manifold, entrance) > TOL else []
    return Routing(trenches, paths, header)


# ---------------------------------------------------------------- drawn trenches

def _project(p: Point, a: Point, b: Point) -> tuple[float, Point]:
    """Parameter (0..1) and point of the projection of p on the segment a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ll = dx * dx + dy * dy
    s = 0.0 if ll == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ll))
    return s, (a[0] + s * dx, a[1] + s * dy)


def _crossing(a: Point, b: Point, c: Point, d: Point) -> tuple[float, float] | None:
    """Parameters on a-b and c-d where the two segments cross (inside both), or None."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    qp = (c[0] - a[0], c[1] - a[1])
    u = (qp[0] * s[1] - qp[1] * s[0]) / den
    v = (qp[0] * r[1] - qp[1] * r[0]) / den
    if 1e-9 < u < 1 - 1e-9 and 1e-9 < v < 1 - 1e-9:
        return u, v
    return None


class _Graph:
    def __init__(self):
        self.points: list[Point] = []
        self.adj: dict[int, dict[int, float]] = {}

    def node(self, p: Point) -> int:
        for i, q in enumerate(self.points):
            if _dist(p, q) < TOL:
                return i
        self.points.append((float(p[0]), float(p[1])))
        self.adj[len(self.points) - 1] = {}
        return len(self.points) - 1

    def edge(self, i: int, j: int) -> None:
        if i != j:
            d = _dist(self.points[i], self.points[j])
            self.adj[i][j] = self.adj[j][i] = d

    def shortest(self, start: int) -> tuple[dict[int, float], dict[int, int]]:
        dist, prev, heap = {start: 0.0}, {}, [(0.0, start)]
        while heap:
            d, i = heapq.heappop(heap)
            if d > dist.get(i, math.inf):
                continue
            for j, w in self.adj[i].items():
                if d + w < dist.get(j, math.inf) - 1e-12:
                    dist[j], prev[j] = d + w, i
                    heapq.heappush(heap, (d + w, j))
        return dist, prev


def drawn_routing(bhes: list[Point], manifold: Point, entrance: Point | None, lines: list[list[Point]],
                  manifold_in_building: bool = False) -> Routing:
    """Route along the drawn trench lines (polylines in metres)."""
    segments = [(tuple(a), tuple(b)) for line in lines for a, b in zip(line, line[1:]) if _dist(a, b) > TOL]
    if not segments:
        return auto_routing(bhes, manifold, None if manifold_in_building else entrance)
    terminals = [manifold, *bhes] + ([entrance] if entrance is not None and not manifold_in_building else [])
    cuts: list[list[float]] = [[0.0, 1.0] for _ in segments]
    for i, (a, b) in enumerate(segments):  # lines crossing each other are joined there
        for j in range(i + 1, len(segments)):
            hit = _crossing(a, b, *segments[j])
            if hit:
                cuts[i].append(hit[0])
                cuts[j].append(hit[1])
    stubs = []
    for p in terminals:  # each terminal joins the nearest trench
        best = min(((k, *_project(p, a, b)) for k, (a, b) in enumerate(segments)), key=lambda x: _dist(p, x[2]))
        cuts[best[0]].append(best[1])
        stubs.append((p, best[2]))
    g = _Graph()
    for (a, b), ss in zip(segments, cuts):
        pts = [(a[0] + s * (b[0] - a[0]), a[1] + s * (b[1] - a[1])) for s in sorted(set(ss))]
        for p, q in zip(pts, pts[1:]):
            g.edge(g.node(p), g.node(q))
    term_nodes = []
    for p, on_line in stubs:
        i, j = g.node(p), g.node(on_line)
        g.edge(i, j)
        term_nodes.append(i)
    dist, prev = g.shortest(term_nodes[0])
    count: dict[tuple[int, int], int] = {}
    paths, unconnected = [], []
    for k, node in enumerate(term_nodes[1:len(bhes) + 1]):
        if node not in dist:
            unconnected.append(k)
            paths.append(_dist(bhes[k], manifold))
            continue
        paths.append(dist[node])
        while node in prev:
            e = (min(node, prev[node]), max(node, prev[node]))
            count[e] = count.get(e, 0) + 1
            node = prev[node]
    trenches = [(g.points[i], g.points[j], c) for (i, j), c in count.items() if _dist(g.points[i], g.points[j]) > TOL]
    trenches += [(manifold, bhes[k], 1) for k in unconnected]
    header: list[Point] = []
    if entrance is not None and not manifold_in_building:
        node = term_nodes[-1]
        if node in dist:
            header = [g.points[node]]
            while node in prev:
                node = prev[node]
                header.append(g.points[node])
            header.reverse()
        else:
            header = [manifold, entrance]
    return Routing(trenches, paths, header, unconnected)


def snap(p: Point, lines: list[list[Point]], current: list[Point], radius: float) -> Point:
    """A clicked point snapped to a nearby vertex of the drawn lines (so lines join), else unchanged."""
    best, best_d = p, radius
    for q in [pt for line in lines for pt in line] + list(current):
        d = _dist(p, q)
        if d < best_d:
            best, best_d = (float(q[0]), float(q[1])), d
    return best
