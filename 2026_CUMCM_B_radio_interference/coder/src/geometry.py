"""Q1 set-membership bearing intersection geometry.

The mathematical model uses only the bounded bearing error stated in the problem.
No probability distribution is assumed.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, pi, radians, sin
from typing import Iterable, List, Optional, Sequence, Tuple

Point = Tuple[float, float]


@dataclass(frozen=True)
class HalfPlane:
    """Closed half-plane a*x + b*y <= c."""

    a: float
    b: float
    c: float
    label: str = ""

    def contains(self, p: Point, tol: float = 1e-8) -> bool:
        return self.a * p[0] + self.b * p[1] <= self.c + tol


def bearing_wedge_halfplanes(
    sensor: Point, theta_deg: float, delta_deg: float = 1.0, label: str = ""
) -> List[HalfPlane]:
    """Return the two half-planes for a forward bearing wedge.

    theta follows the problem convention: 0 deg east, counter-clockwise positive.
    """
    sx, sy = sensor
    lo = radians(theta_deg - delta_deg)
    hi = radians(theta_deg + delta_deg)

    # cross(u_lo, p-S) >= 0
    # -> sin(lo)*x - cos(lo)*y <= sin(lo)*sx - cos(lo)*sy
    hp_lo = HalfPlane(
        sin(lo),
        -cos(lo),
        sin(lo) * sx - cos(lo) * sy,
        f"{label}:lower" if label else "lower",
    )

    # cross(u_hi, p-S) <= 0
    # -> -sin(hi)*x + cos(hi)*y <= -sin(hi)*sx + cos(hi)*sy
    hp_hi = HalfPlane(
        -sin(hi),
        cos(hi),
        -sin(hi) * sx + cos(hi) * sy,
        f"{label}:upper" if label else "upper",
    )
    return [hp_lo, hp_hi]


def line_intersection(h1: HalfPlane, h2: HalfPlane, tol: float = 1e-12) -> Optional[Point]:
    det = h1.a * h2.b - h2.a * h1.b
    if abs(det) <= tol:
        return None
    x = (h1.c * h2.b - h2.c * h1.b) / det
    y = (h1.a * h2.c - h2.a * h1.c) / det
    return (x, y)


def _dedupe(points: Iterable[Point], tol: float = 1e-7) -> List[Point]:
    out: List[Point] = []
    for p in points:
        if not any(hypot(p[0] - q[0], p[1] - q[1]) <= tol for q in out):
            out.append(p)
    return out


def convex_hull(points: Sequence[Point]) -> List[Point]:
    """Monotone-chain convex hull, CCW, without repeated first point."""
    pts = sorted(set((float(x), float(y)) for x, y in points))
    if len(pts) <= 1:
        return pts

    def cross(o: Point, a: Point, b: Point) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Point] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 1e-10:
            lower.pop()
        lower.append(p)

    upper: List[Point] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 1e-10:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def has_recession_direction(halfplanes: Sequence[HalfPlane], tol: float = 1e-10) -> bool:
    """Check whether Ax<=b has a non-zero feasible recession direction.

    In 2D the angular feasible set is an intersection of closed semicircles.
    If non-empty, at least one boundary direction n_i +/- 90 deg is feasible.
    """
    if not halfplanes:
        return True
    candidates: List[float] = []
    for h in halfplanes:
        if abs(h.a) + abs(h.b) <= tol:
            continue
        ang = atan2(h.b, h.a)
        candidates.extend([ang + pi / 2, ang - pi / 2])
    for phi in candidates:
        dx, dy = cos(phi), sin(phi)
        if all(h.a * dx + h.b * dy <= tol for h in halfplanes):
            return True
    return False


@dataclass
class LocalizationRegion:
    status: str  # EMPTY / UNBOUNDED / BOUNDED
    vertices: List[Point]
    halfplanes: List[HalfPlane]

    @property
    def diameter(self) -> float:
        if self.status == "UNBOUNDED":
            return float("inf")
        if self.status == "EMPTY" or len(self.vertices) <= 1:
            return 0.0
        return polygon_diameter(self.vertices)[0]


def localization_region(
    sensors: Sequence[Point], bearings_deg: Sequence[float], delta_deg: float = 1.0
) -> LocalizationRegion:
    if len(sensors) != len(bearings_deg):
        raise ValueError("sensors and bearings_deg must have the same length")
    if not sensors:
        return LocalizationRegion("UNBOUNDED", [], [])

    hps: List[HalfPlane] = []
    for i, (s, th) in enumerate(zip(sensors, bearings_deg)):
        hps.extend(bearing_wedge_halfplanes(s, th, delta_deg, label=f"S{i}"))

    candidates: List[Point] = []
    for i in range(len(hps)):
        for j in range(i + 1, len(hps)):
            p = line_intersection(hps[i], hps[j])
            if p is not None and all(h.contains(p) for h in hps):
                candidates.append(p)

    # Sensor points / origin can expose feasible degenerate vertices missed by nearly-parallel pairs.
    for p in list(sensors) + [(0.0, 0.0)]:
        if all(h.contains(p) for h in hps):
            candidates.append(p)

    feasible = _dedupe(candidates)
    unbounded = has_recession_direction(hps)

    if not feasible:
        # With bearing wedges a non-empty pointed polyhedron has an extreme point.  If no
        # feasible boundary intersection exists, classify as EMPTY; this is also the safe
        # response for inconsistent measured wedges.
        return LocalizationRegion("EMPTY", [], hps)
    if unbounded:
        return LocalizationRegion("UNBOUNDED", convex_hull(feasible), hps)
    return LocalizationRegion("BOUNDED", convex_hull(feasible), hps)


def polygon_diameter(vertices: Sequence[Point]) -> Tuple[float, Tuple[Point, Point]]:
    if not vertices:
        return 0.0, ((0.0, 0.0), (0.0, 0.0))
    if len(vertices) == 1:
        return 0.0, (vertices[0], vertices[0])
    best_d2 = -1.0
    best_pair = (vertices[0], vertices[1])
    for i in range(len(vertices)):
        for j in range(i + 1, len(vertices)):
            dx = vertices[i][0] - vertices[j][0]
            dy = vertices[i][1] - vertices[j][1]
            d2 = dx * dx + dy * dy
            if d2 > best_d2:
                best_d2 = d2
                best_pair = (vertices[i], vertices[j])
    return best_d2 ** 0.5, best_pair


def _circumcircle(a: Point, b: Point, c: Point, tol: float = 1e-12):
    """Return circumcenter/radius for three non-collinear points, else None."""
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) <= tol:
        return None
    a2 = ax * ax + ay * ay
    b2 = bx * bx + by * by
    c2 = cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    center = (ux, uy)
    return center, hypot(ux - ax, uy - ay)


def minimum_enclosing_circle(points: Sequence[Point], tol: float = 1e-8):
    """Exact minimum enclosing circle for a small 2-D point set.

    A Euclidean minimum enclosing circle is supported by at most three boundary points.
    Localization polygons in this task have very few vertices, so enumerating all one-,
    two-, and three-point support circles is simpler and more auditable than a randomized
    Welzl implementation.  Covering the polygon vertices also covers the whole convex polygon.
    """
    pts = list(points)
    if not pts:
        return (0.0, 0.0), 0.0
    if len(pts) == 1:
        return pts[0], 0.0

    def covers(center: Point, radius: float) -> bool:
        return all(hypot(p[0] - center[0], p[1] - center[1]) <= radius + tol for p in pts)

    best_center = pts[0]
    best_radius = float("inf")

    # Two-point support circles.
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            c = ((pts[i][0] + pts[j][0]) / 2.0, (pts[i][1] + pts[j][1]) / 2.0)
            r = hypot(pts[i][0] - c[0], pts[i][1] - c[1])
            if r < best_radius and covers(c, r):
                best_center, best_radius = c, r

    # Three-point support circles.
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            for k in range(j + 1, len(pts)):
                cc = _circumcircle(pts[i], pts[j], pts[k])
                if cc is None:
                    continue
                c, r = cc
                if r < best_radius and covers(c, r):
                    best_center, best_radius = c, r

    # Numerically degenerate collinear sets are always covered by a diameter-pair circle.
    if best_radius == float("inf"):
        _, (a, b) = polygon_diameter(pts)
        best_center = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        best_radius = hypot(a[0] - best_center[0], a[1] - best_center[1])
    return best_center, best_radius


def diameter_circle_covers(vertices: Sequence[Point], tol: float = 1e-8):
    """Whether *some* circle of diameter equal to the set diameter covers all vertices.

    Any such circle must contain a diametral pair a,b separated by D. Equal radius D/2
    disks around a and b touch at only their midpoint, so the center is forced to (a+b)/2.
    """
    if not vertices:
        return True, (0.0, 0.0), 0.0
    D, (a, b) = polygon_diameter(vertices)
    c = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
    r = D / 2.0
    ok = all(hypot(v[0] - c[0], v[1] - c[1]) <= r + tol for v in vertices)
    return ok, c, r


def point_satisfies_region(p: Point, region: LocalizationRegion, tol: float = 1e-8) -> bool:
    return all(h.contains(p, tol=tol) for h in region.halfplanes)
