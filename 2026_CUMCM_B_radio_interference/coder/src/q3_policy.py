"""Q3 guaranteed omni-source discovery/localization/clear policy.

The online policy uses only responses exposed by the simulator. Ground-truth Source objects are
never inspected.  Guarantee structure:
  1) every unresolved channel is eventually measured at a 7-point 1000-m covering set;
  2) a detected channel is localized with bounded-bearing intersections;
  3) /clear is issued only when the localization polygon's exact minimum enclosing circle has
     radius <=20 m (except the explicit `near` case).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot
from typing import Dict, List, Optional, Tuple

from geometry import localization_region, minimum_enclosing_circle, polygon_diameter
from q2_candidate_region import conservative_max_distance, robust_symmetric_second_points
from search_policy import omni_guaranteed_scan_points

Point = Tuple[float, float]

# API svd_deg is rounded to 0.01 deg. If the underlying physical error can reach exactly
# +/-1 deg, formatting can add at most 0.005 deg. Keep Q1 mathematics at 1 deg, but use a
# 1.005-deg runtime envelope for protocol-robust set intersection.
RUNTIME_BEARING_DELTA_DEG = 1.005


@dataclass
class DetectedTarget:
    channel: int
    sensors: List[Point] = field(default_factory=list)
    bearings: List[float] = field(default_factory=list)
    cleared: bool = False


@dataclass
class PolicyStats:
    cleared_channels: List[int] = field(default_factory=list)
    measure_calls: int = 0
    clear_calls: int = 0
    no_signal_calls: int = 0
    near_calls: int = 0
    direction_calls: int = 0
    anomalies: List[str] = field(default_factory=list)
    last_position: Point = (0.0, 0.0)
    virtual_time_s: float = 0.0


def _measure(api, stats: PolicyStats, p: Point, ch: int):
    r = api.measure(p[0], p[1], ch)
    stats.measure_calls += 1
    stats.last_position = p
    stats.virtual_time_s = float(r.get("virtual_time_s", stats.virtual_time_s))
    kind = r.get("measure_result")
    if kind == "no_signal":
        stats.no_signal_calls += 1
    elif kind == "near":
        stats.near_calls += 1
    elif kind == "direction":
        stats.direction_calls += 1
    return r


def _clear(api, stats: PolicyStats, p: Point, ch: int):
    r = api.clear(p[0], p[1], ch)
    stats.clear_calls += 1
    stats.last_position = p
    stats.virtual_time_s = float(r.get("virtual_time_s", stats.virtual_time_s))
    if r.get("clear_result") == "success" and ch not in stats.cleared_channels:
        stats.cleared_channels.append(ch)
    return r


def _next_polygon_probe(vertices: List[Point], current: Point) -> Point:
    center, radius = minimum_enclosing_circle(vertices)
    D, (a, b) = polygon_diameter(vertices)
    if D <= 1e-9:
        normal = (1.0, 0.0)
    else:
        ux, uy = (b[0] - a[0]) / D, (b[1] - a[1]) / D
        normal = (-uy, ux)
    # Every true source is in MEC(center,radius).  A point L from center is at most L+radius
    # from the source, so L<=1000-radius guarantees an omni signal under R_min=1000.
    L = min(800.0, max(50.0, 1000.0 - radius - 1.0))
    p1 = (center[0] + L * normal[0], center[1] + L * normal[1])
    p2 = (center[0] - L * normal[0], center[1] - L * normal[1])
    return min((p1, p2), key=lambda p: hypot(p[0] - current[0], p[1] - current[1]))


def localize_and_clear_omni(
    api,
    target: DetectedTarget,
    stats: PolicyStats,
    max_direction_measurements: int = 6,
) -> bool:
    ch = target.channel
    if target.cleared:
        return True
    if not target.bearings:
        return False

    # The first reading implies the source is in a <=1500 m, ±1° sector.  Either symmetric
    # point returned here lies within 1000 m of every point in the conservative sector.
    p_plus, p_minus = robust_symmetric_second_points(target.sensors[0], target.bearings[0], delta_deg=RUNTIME_BEARING_DELTA_DEG)
    candidates = sorted((p_plus, p_minus), key=lambda p: hypot(p[0] - stats.last_position[0], p[1] - stats.last_position[1]))

    if len(target.bearings) == 1:
        got_second = False
        for p in candidates:
            r = _measure(api, stats, p, ch)
            if r.get("measure_result") == "near":
                got_second = True
                if _clear(api, stats, p, ch).get("clear_result") == "success":
                    target.cleared = True
                    return True
            elif r.get("measure_result") == "direction":
                target.sensors.append(p)
                target.bearings.append(float(r["svd_deg"]))
                got_second = True
                break
            else:
                stats.anomalies.append(f"Q3 ch={ch}: conservative second point returned no_signal")
        if not got_second:
            return False

    local_iterations = 0
    while local_iterations < max_direction_measurements:
        local_iterations += 1
        reg = localization_region(target.sensors, target.bearings, RUNTIME_BEARING_DELTA_DEG)
        if reg.status != "BOUNDED" or not reg.vertices:
            # Multiple route-scan bearings can still be nearly parallel. Add a deliberately
            # transverse, guaranteed-reception point derived from the first observation.
            extra = None
            for p in candidates:
                if all(hypot(p[0]-q[0], p[1]-q[1]) > 1e-6 for q in target.sensors):
                    extra = p
                    break
            if extra is None:
                stats.anomalies.append(f"Q3 ch={ch}: localization status={reg.status} with no fallback point")
                return False
            r = _measure(api, stats, extra, ch)
            if r.get("measure_result") == "near":
                if _clear(api, stats, extra, ch).get("clear_result") == "success":
                    target.cleared = True
                    return True
            elif r.get("measure_result") == "direction":
                target.sensors.append(extra)
                target.bearings.append(float(r["svd_deg"]))
                continue
            else:
                stats.anomalies.append(f"Q3 ch={ch}: unbounded fallback returned no_signal")
                return False
        center, radius = minimum_enclosing_circle(reg.vertices)
        if radius <= 20.0 + 1e-8:
            cr = _clear(api, stats, center, ch)
            if cr.get("clear_result") == "success":
                target.cleared = True
                return True
            stats.anomalies.append(f"Q3 ch={ch}: guaranteed MEC clear failed at r={radius:.6f}")
            # Preserve evidence and take a new measurement from the failed-clear center.
            r = _measure(api, stats, center, ch)
            if r.get("measure_result") == "near":
                continue
            if r.get("measure_result") == "direction":
                target.sensors.append(center)
                target.bearings.append(float(r["svd_deg"]))
                continue
            return False

        probe = _next_polygon_probe(reg.vertices, stats.last_position)
        r = _measure(api, stats, probe, ch)
        if r.get("measure_result") == "near":
            if _clear(api, stats, probe, ch).get("clear_result") == "success":
                target.cleared = True
                return True
        elif r.get("measure_result") == "direction":
            target.sensors.append(probe)
            target.bearings.append(float(r["svd_deg"]))
        else:
            stats.anomalies.append(f"Q3 ch={ch}: guaranteed polygon probe returned no_signal")
            return False
    stats.anomalies.append(f"Q3 ch={ch}: localization iteration cap reached")
    return False


def _target_already_localized(target: DetectedTarget) -> bool:
    if len(target.bearings) < 2:
        return False
    reg = localization_region(target.sensors, target.bearings, RUNTIME_BEARING_DELTA_DEG)
    if reg.status != "BOUNDED" or not reg.vertices:
        return False
    _, radius = minimum_enclosing_circle(reg.vertices)
    return radius <= 20.0 + 1e-8


def _needs_zero_move_guard_bearing(target: DetectedTarget, guard: Point) -> bool:
    """Whether a guard-site bearing is guaranteed and still useful for localization."""
    if target.cleared or not target.bearings:
        return False
    if len(target.bearings) == 1:
        return conservative_max_distance(target.sensors[0], target.bearings[0], guard, delta_deg=RUNTIME_BEARING_DELTA_DEG) <= 1000.0 + 1e-8
    reg = localization_region(target.sensors, target.bearings, RUNTIME_BEARING_DELTA_DEG)
    if reg.status != "BOUNDED" or not reg.vertices:
        return conservative_max_distance(target.sensors[0], target.bearings[0], guard, delta_deg=RUNTIME_BEARING_DELTA_DEG) <= 1000.0 + 1e-8
    _, radius = minimum_enclosing_circle(reg.vertices)
    if radius <= 20.0 + 1e-8:
        return False
    return max(hypot(guard[0]-v[0], guard[1]-v[1]) for v in reg.vertices) <= 1000.0 + 1e-8


def _nearest_unvisited(points: List[Point], current: Point) -> int:
    return min(range(len(points)), key=lambda i: hypot(points[i][0] - current[0], points[i][1] - current[1]))


def run_q3_policy(api, defer_localization_until_scan_complete: bool = False, skip_detected_during_cover: bool = False, harvest_localization_during_cover: bool = False, opportunistic_until_localized: bool = False) -> PolicyStats:
    """Execute the guaranteed Q3 policy after the caller has entered the simulator."""
    stats = PolicyStats()
    targets: Dict[int, DetectedTarget] = {}
    remaining_scan_points = list(omni_guaranteed_scan_points())
    reverse_channels = False

    while remaining_scan_points:
        idx = _nearest_unvisited(remaining_scan_points, stats.last_position)
        p = remaining_scan_points.pop(idx)
        unresolved = []
        for ch in range(1, 21):
            if ch in stats.cleared_channels:
                continue
            if ch not in targets:
                unresolved.append(ch)
                continue
            if skip_detected_during_cover:
                continue
            if opportunistic_until_localized:
                if not _target_already_localized(targets[ch]):
                    unresolved.append(ch)
            elif harvest_localization_during_cover:
                if _needs_zero_move_guard_bearing(targets[ch], p):
                    unresolved.append(ch)
            else:
                unresolved.append(ch)
        order = list(reversed(unresolved)) if reverse_channels else unresolved
        reverse_channels = not reverse_channels

        discovered_here: List[int] = []
        for ch in order:
            r = _measure(api, stats, p, ch)
            kind = r.get("measure_result")
            if kind == "near":
                if _clear(api, stats, p, ch).get("clear_result") == "success":
                    targets.setdefault(ch, DetectedTarget(ch)).cleared = True
            elif kind == "direction":
                t = targets.setdefault(ch, DetectedTarget(ch))
                t.sensors.append(p)
                t.bearings.append(float(r["svd_deg"]))
                if ch not in discovered_here:
                    discovered_here.append(ch)

        if len(stats.cleared_channels) >= 16:
            break

        if not defer_localization_until_scan_complete:
            # Greedy nearest expected second-probe route; all targets are still guaranteed to
            # be found because unresolved channels resume the finite covering scan afterwards.
            pending = [targets[ch] for ch in discovered_here if not targets[ch].cleared]
            while pending:
                def entry_cost(t: DetectedTarget):
                    a, b = robust_symmetric_second_points(t.sensors[0], t.bearings[0], delta_deg=RUNTIME_BEARING_DELTA_DEG)
                    return min(hypot(a[0] - stats.last_position[0], a[1] - stats.last_position[1]),
                               hypot(b[0] - stats.last_position[0], b[1] - stats.last_position[1]))
                t = min(pending, key=entry_cost)
                localize_and_clear_omni(api, t, stats)
                pending.remove(t)
                if len(stats.cleared_channels) >= 16:
                    break

    # Any detected but uncleared targets are now handled. Remaining unseen channels have been
    # measured on the full 7-point cover and therefore cannot contain an omni source.
    pending = [t for t in targets.values() if not t.cleared]
    while pending:
        def service_cost(t: DetectedTarget) -> float:
            if len(t.bearings) >= 2:
                reg = localization_region(t.sensors, t.bearings, 1.0)
                if reg.status == "BOUNDED" and reg.vertices:
                    c, _ = minimum_enclosing_circle(reg.vertices)
                    return hypot(c[0]-stats.last_position[0], c[1]-stats.last_position[1])
            a, b = robust_symmetric_second_points(t.sensors[0], t.bearings[0], delta_deg=RUNTIME_BEARING_DELTA_DEG)
            return min(hypot(a[0]-stats.last_position[0], a[1]-stats.last_position[1]),
                       hypot(b[0]-stats.last_position[0], b[1]-stats.last_position[1]))
        t = min(pending, key=service_cost)
        localize_and_clear_omni(api, t, stats)
        pending.remove(t)
    return stats
