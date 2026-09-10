"""Q2 second-measurement candidate-region construction.

This module deliberately keeps the source-position distribution configurable because the
problem statement specifies only bounded geometry, not a probability law.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan2, cos, hypot, pi, radians, sin, sqrt
from random import Random
from typing import List, Sequence, Tuple

Point = Tuple[float, float]


def angle_wrap_rad(x: float) -> float:
    while x <= -pi:
        x += 2 * pi
    while x > pi:
        x -= 2 * pi
    return x


def ray_disk_interval(sensor: Point, phi: float, disk_radius: float = 1800.0):
    """Positive t interval for sensor+t*u(phi) inside origin-centered disk."""
    sx, sy = sensor
    ux, uy = cos(phi), sin(phi)
    b = sx * ux + sy * uy
    c = sx * sx + sy * sy - disk_radius * disk_radius
    disc = b * b - c
    if disc < 0:
        return None
    q = sqrt(max(0.0, disc))
    t1, t2 = -b - q, -b + q
    lo, hi = max(0.0, t1), t2
    if hi < lo:
        return None
    return lo, hi


def sample_first_feasible_region(
    sensor: Point,
    bearing_deg: float,
    n: int = 1000,
    delta_deg: float = 1.0,
    target_radius: float = 1800.0,
    max_receive_radius: float = 1500.0,
    min_direction_distance: float = 5.0,
    seed: int = 20260910,
) -> List[Point]:
    """Area-like samples from Omega1 using polar-angle/r^2 sampling.

    This is a design prior only. It is not asserted to be the simulator's source distribution.
    """
    rng = Random(seed)
    out: List[Point] = []
    th0 = radians(bearing_deg)
    delta = radians(delta_deg)
    attempts = 0
    while len(out) < n and attempts < 20 * n:
        attempts += 1
        phi = th0 + rng.uniform(-delta, delta)
        iv = ray_disk_interval(sensor, phi, target_radius)
        if iv is None:
            continue
        lo = max(min_direction_distance, iv[0])
        hi = min(max_receive_radius, iv[1])
        if hi <= lo:
            continue
        # r dr area element -> uniform in r^2.
        r = sqrt(rng.uniform(lo * lo, hi * hi))
        out.append((sensor[0] + r * cos(phi), sensor[1] + r * sin(phi)))
    if not out:
        raise ValueError("First bearing wedge has no feasible point in target disk")
    return out


def crossing_angle_rad(s1: Point, s2: Point, g: Point) -> float:
    """Acute intersection angle between the two bearing lines at G."""
    v1 = (s1[0] - g[0], s1[1] - g[1])
    v2 = (s2[0] - g[0], s2[1] - g[1])
    n1, n2 = hypot(*v1), hypot(*v2)
    if n1 <= 1e-12 or n2 <= 1e-12:
        return pi / 2
    c = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    a = acos(c)
    return min(a, pi - a)


@dataclass(frozen=True)
class CandidateScore:
    point: Point
    score: float
    guaranteed_detection_rate: float
    mean_sin2_angle: float
    q10_angle_deg: float
    median_angle_deg: float
    move_distance: float


def _quantile(xs: Sequence[float], q: float) -> float:
    ys = sorted(xs)
    if not ys:
        return 0.0
    idx = int(round(q * (len(ys) - 1)))
    return ys[max(0, min(len(ys) - 1, idx))]


def score_candidate(
    s1: Point,
    s2: Point,
    source_samples: Sequence[Point],
    guaranteed_receive_radius: float = 1000.0,
    travel_lambda: float = 0.08,
) -> CandidateScore:
    qualities: List[float] = []
    angles_deg: List[float] = []
    detected = 0
    for g in source_samples:
        a = crossing_angle_rad(s1, s2, g)
        angles_deg.append(a * 180.0 / pi)
        q = sin(a) ** 2
        if hypot(s2[0] - g[0], s2[1] - g[1]) <= guaranteed_receive_radius + 1e-9:
            detected += 1
            qualities.append(q)
        else:
            qualities.append(0.0)
    rate = detected / len(source_samples)
    mean_q = sum(qualities) / len(qualities)
    move = hypot(s2[0] - s1[0], s2[1] - s1[1])
    score = mean_q - travel_lambda * move / 1000.0
    return CandidateScore(
        point=s2,
        score=score,
        guaranteed_detection_rate=rate,
        mean_sin2_angle=mean_q,
        q10_angle_deg=_quantile(angles_deg, 0.10),
        median_angle_deg=_quantile(angles_deg, 0.50),
        move_distance=move,
    )


def generate_candidates(
    s1: Point,
    bearing_deg: float,
    max_move: float = 1000.0,
    radial_step: float = 100.0,
    angle_step_deg: float = 15.0,
) -> List[Point]:
    """Generic candidate fan around S1; robot may legally move outside target disk."""
    out = [s1]
    r = radial_step
    th0 = radians(bearing_deg)
    while r <= max_move + 1e-9:
        d = -180.0
        while d < 180.0 - 1e-9:
            phi = th0 + radians(d)
            out.append((s1[0] + r * cos(phi), s1[1] + r * sin(phi)))
            d += angle_step_deg
        r += radial_step
    return out


def recommend_second_point(
    s1: Point,
    bearing_deg: float,
    n_source_samples: int = 1000,
    min_guarantee_rate: float = 0.60,
    seed: int = 20260910,
) -> Tuple[CandidateScore, List[CandidateScore]]:
    samples = sample_first_feasible_region(s1, bearing_deg, n_source_samples, seed=seed)
    scored = [score_candidate(s1, p, samples) for p in generate_candidates(s1, bearing_deg) if p != s1]
    feasible = [s for s in scored if s.guaranteed_detection_rate >= min_guarantee_rate]
    pool = feasible if feasible else scored
    pool.sort(key=lambda s: (s.score, s.guaranteed_detection_rate, s.q10_angle_deg), reverse=True)
    return pool[0], pool[:50]


# ---------------------------------------------------------------------------
# Distribution-free conservative design used as the Q2 primary strategy.
# ---------------------------------------------------------------------------

def conservative_sector_corners(
    s1: Point,
    bearing_deg: float,
    r_min: float = 5.0,
    r_max: float = 1500.0,
    delta_deg: float = 1.0,
) -> List[Point]:
    """Four extreme points of a conservative first-measurement sector.

    The true feasible set is further clipped by the radius-1800 target disk, so using the
    complete annular sector is conservative. A second site within 1000 m of every point in
    this sector is guaranteed to receive an omni source regardless of its unknown receive
    radius in [1000,1500].
    """
    out: List[Point] = []
    for r in (r_min, r_max):
        for e in (-delta_deg, delta_deg):
            a = radians(bearing_deg + e)
            out.append((s1[0] + r * cos(a), s1[1] + r * sin(a)))
    return out


def conservative_max_distance(
    s1: Point,
    bearing_deg: float,
    s2: Point,
    r_min: float = 5.0,
    r_max: float = 1500.0,
    delta_deg: float = 1.0,
) -> float:
    """Exact max distance from S2 to the conservative annular sector.

    For fixed angle squared distance is convex in r, hence its maximum is at r_min/r_max.
    Over the 2-degree angular interval the minimum projection onto S2-S1, and therefore the
    maximum distance, occurs at an angular endpoint. Thus the four sector corners suffice.
    """
    return max(
        hypot(s2[0] - g[0], s2[1] - g[1])
        for g in conservative_sector_corners(s1, bearing_deg, r_min, r_max, delta_deg)
    )


def guaranteed_second_point_region_test(
    s1: Point,
    bearing_deg: float,
    s2: Point,
    guaranteed_receive_radius: float = 1000.0,
    max_move: float | None = 1000.0,
) -> bool:
    """Membership test for the distribution-free Q2 candidate region."""
    if max_move is not None and hypot(s2[0] - s1[0], s2[1] - s1[1]) > max_move + 1e-9:
        return False
    return conservative_max_distance(s1, bearing_deg, s2) <= guaranteed_receive_radius + 1e-9


def robust_symmetric_second_points(
    s1: Point,
    bearing_deg: float,
    r_min: float = 5.0,
    r_max: float = 1500.0,
    delta_deg: float = 1.0,
    guaranteed_receive_radius: float = 1000.0,
    max_move: float = 1000.0,
) -> Tuple[Point, Point]:
    """Return a symmetric, distribution-free pair of strong Q2 candidates.

    Put the axial coordinate at the midrange of possible source distance, then push laterally
    as far as allowed by both the 1000-m guaranteed-detection condition and the move budget.
    The construction is deterministic and does not require a source-position probability law.
    """
    m = 0.5 * (r_min + r_max)
    e = (cos(radians(bearing_deg)), sin(radians(bearing_deg)))
    nvec = (-e[1], e[0])

    def point(h: float) -> Point:
        return (s1[0] + m * e[0] + h * nvec[0], s1[1] + m * e[1] + h * nvec[1])

    h_travel = sqrt(max(0.0, max_move * max_move - m * m))
    lo, hi = 0.0, guaranteed_receive_radius + max_move
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if conservative_max_distance(s1, bearing_deg, point(mid), r_min, r_max, delta_deg) <= guaranteed_receive_radius:
            lo = mid
        else:
            hi = mid
    h = min(h_travel, lo)
    return point(h), point(-h)
