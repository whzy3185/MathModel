"""Geometric building blocks for Q3/Q4 search policies."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, pi, sin, sqrt
from typing import Dict, List, Tuple

Point = Tuple[float, float]


def omni_guaranteed_scan_points(target_radius: float = 1800.0, min_receive_radius: float = 1000.0) -> List[Point]:
    """Center + six shortest-radius symmetric ring points guaranteeing Q3 discovery.

    Center covers rho<=r. For rho>=r, the worst azimuth is 30 deg from a ring point.
    The lower root makes the target boundary exactly r from that nearest ring point.
    """
    R, r = target_radius, min_receive_radius
    disc = r * r - R * R * sin(pi / 6) ** 2
    if disc < 0:
        raise ValueError("Six-point ring cannot satisfy the requested radii")
    a = R * cos(pi / 6) - sqrt(disc)
    pts = [(0.0, 0.0)]
    for k in range(6):
        phi = k * pi / 3
        pts.append((a * cos(phi), a * sin(phi)))
    return pts


def triangular_directional_scan_points(
    target_radius: float = 1800.0, spacing: float = 1000.0
) -> List[Point]:
    """Safe triangular-lattice patch for Q4 directional discovery.

    All lattice vertices within R+s are retained. Any target point lies in an infinite-lattice
    triangle of side s; each of that triangle's vertices is <=s from the source and <=R+s from
    the origin, hence is included. Since the source is inside their convex hull, any closed
    half-plane through the source contains at least one vertex.
    """
    if spacing > 1000.0 + 1e-9:
        raise ValueError("spacing must be <=1000 m for the min receive-radius guarantee")
    R, s = target_radius, spacing
    h = sqrt(3.0) * s / 2.0
    bound = R + s
    jmax = int(bound / h) + 2
    imax = int(bound / s) + 3
    pts: List[Point] = []
    for j in range(-jmax, jmax + 1):
        y = j * h
        offset = (j & 1) * s / 2.0
        for i in range(-imax, imax + 1):
            x = i * s + offset
            if x * x + y * y <= bound * bound + 1e-8:
                pts.append((round(x, 9), round(y, 9)))
    return sorted(set(pts))


@dataclass
class TargetState:
    channel: int
    state: str = "UNKNOWN"
    measurements: List[Tuple[Point, str, float | None]] = field(default_factory=list)
    cleared: bool = False
    failed_clear_positions: List[Point] = field(default_factory=list)


class ChannelRegistry:
    def __init__(self):
        self.targets: Dict[int, TargetState] = {ch: TargetState(ch) for ch in range(1, 21)}

    def cleared_count(self) -> int:
        return sum(t.cleared for t in self.targets.values())

    def can_stop_by_upper_bound(self) -> bool:
        return self.cleared_count() >= 16
