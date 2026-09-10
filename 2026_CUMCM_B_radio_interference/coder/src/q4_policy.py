"""Q4 robust policy for mixed omni/directional sources.

Discovery guarantee:
A directional source covers a closed half-plane through itself.  If G is inside a triangular
cell with side <=1000 m, all three cell vertices are within the minimum receive radius and at
least one vertex lies in every closed half-plane through G.  Therefore scanning a triangular
lattice patch guarantees at least one visible reading for every source, independent of beam
direction.

Clear fallback guarantee:
From any visible point S, first try /clear. If it fails, r=|SG|>20. For measured bearing theta
with true bearing inside theta +/- delta, probe the two wedge-boundary points at q<20 m. Their
chord intersects every possible true ray before G. Since the visible set is a convex half-plane
containing S and G, at least one probe is visible. Both probes are also closer to G than S, so
repeating strictly approaches the source. This is a slow but deterministic fallback; free
bearings collected on the global scan often allow direct MEC-based clear before it is needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import cos, hypot, radians, sin
from typing import Dict, List, Tuple

from geometry import localization_region, minimum_enclosing_circle
from search_policy import triangular_directional_scan_points

Point = Tuple[float, float]
RUNTIME_BEARING_DELTA_DEG = 1.005


@dataclass
class DirectionalTarget:
    channel: int
    sensors: List[Point] = field(default_factory=list)
    bearings: List[float] = field(default_factory=list)
    cleared: bool = False


@dataclass
class Q4Stats:
    cleared_channels: List[int] = field(default_factory=list)
    measure_calls: int = 0
    clear_calls: int = 0
    no_signal_calls: int = 0
    direction_calls: int = 0
    near_calls: int = 0
    fallback_steps: int = 0
    anomalies: List[str] = field(default_factory=list)
    last_position: Point = (0.0, 0.0)
    virtual_time_s: float = 0.0


def _measure(api, st: Q4Stats, p: Point, ch: int):
    r=api.measure(p[0],p[1],ch); st.measure_calls+=1;st.last_position=p
    st.virtual_time_s=float(r.get('virtual_time_s',st.virtual_time_s))
    k=r.get('measure_result')
    if k=='no_signal':st.no_signal_calls+=1
    elif k=='direction':st.direction_calls+=1
    elif k=='near':st.near_calls+=1
    return r


def _clear(api, st: Q4Stats, p: Point, ch: int):
    r=api.clear(p[0],p[1],ch);st.clear_calls+=1;st.last_position=p
    st.virtual_time_s=float(r.get('virtual_time_s',st.virtual_time_s))
    if r.get('clear_result')=='success' and ch not in st.cleared_channels:st.cleared_channels.append(ch)
    return r


def _target_mec(target: DirectionalTarget):
    if len(target.bearings)<2:return None
    reg=localization_region(target.sensors,target.bearings,RUNTIME_BEARING_DELTA_DEG)
    if reg.status!='BOUNDED' or not reg.vertices:return None
    return minimum_enclosing_circle(reg.vertices)


def _localized(target: DirectionalTarget)->bool:
    m=_target_mec(target)
    return m is not None and m[1]<=20.0+1e-8


def _safe_probe_pair(s:Point,bearing:float,step:float=19.5):
    d=RUNTIME_BEARING_DELTA_DEG
    out=[]
    for sign in (-1.0,1.0):
        a=radians(bearing+sign*d)
        out.append((s[0]+step*cos(a),s[1]+step*sin(a)))
    return out[0],out[1]


def directional_fallback_clear(api,target:DirectionalTarget,st:Q4Stats,max_steps:int=90)->bool:
    """Guaranteed short-step chase, assuming target has at least one stored visible bearing."""
    ch=target.channel
    # Prefer a visible observation close to current robot position.
    idx=min(range(len(target.sensors)),key=lambda i:hypot(target.sensors[i][0]-st.last_position[0],target.sensors[i][1]-st.last_position[1]))
    s=target.sensors[idx];bearing=target.bearings[idx]
    for _ in range(max_steps):
        cr=_clear(api,st,s,ch)
        if cr.get('clear_result')=='success':target.cleared=True;return True
        p1,p2=_safe_probe_pair(s,bearing)
        # If first is blind, the second is guaranteed visible by the chord/half-plane proof.
        for p in (p1,p2):
            mr=_measure(api,st,p,ch)
            if mr.get('measure_result')=='near':
                if _clear(api,st,p,ch).get('clear_result')=='success':target.cleared=True;return True
            elif mr.get('measure_result')=='direction':
                s=p;bearing=float(mr['svd_deg']);target.sensors.append(p);target.bearings.append(bearing)
                st.fallback_steps+=1
                break
        else:
            st.anomalies.append(f'Q4 ch={ch}: both safe directional probes were no_signal')
            return False
        # Accumulated chase bearings may already tightly localize the source.
        m=_target_mec(target)
        if m is not None and m[1]<=20.0+1e-8:
            if _clear(api,st,m[0],ch).get('clear_result')=='success':target.cleared=True;return True
    st.anomalies.append(f'Q4 ch={ch}: fallback step cap reached')
    return False


def run_q4_policy(api,spacing:float=1000.0)->Q4Stats:
    st=Q4Stats();targets:Dict[int,DirectionalTarget]={}
    remaining=list(triangular_directional_scan_points(spacing=spacing))
    reverse=False
    while remaining:
        idx=min(range(len(remaining)),key=lambda i:hypot(remaining[i][0]-st.last_position[0],remaining[i][1]-st.last_position[1]))
        p=remaining.pop(idx)
        channels=[]
        for ch in range(1,21):
            if ch in st.cleared_channels:continue
            if ch not in targets or not _localized(targets[ch]):channels.append(ch)
        order=list(reversed(channels)) if reverse else channels;reverse=not reverse
        for ch in order:
            mr=_measure(api,st,p,ch);kind=mr.get('measure_result')
            if kind=='near':
                if _clear(api,st,p,ch).get('clear_result')=='success':
                    targets.setdefault(ch,DirectionalTarget(ch)).cleared=True
            elif kind=='direction':
                t=targets.setdefault(ch,DirectionalTarget(ch));t.sensors.append(p);t.bearings.append(float(mr['svd_deg']))
        if len(st.cleared_channels)>=16:break

    pending=[t for t in targets.values() if not t.cleared]
    while pending:
        def cost(t:DirectionalTarget):
            m=_target_mec(t)
            if m is not None:return hypot(m[0][0]-st.last_position[0],m[0][1]-st.last_position[1])
            return min(hypot(p[0]-st.last_position[0],p[1]-st.last_position[1]) for p in t.sensors)
        t=min(pending,key=cost)
        m=_target_mec(t)
        if m is not None and m[1]<=20.0+1e-8:
            if _clear(api,st,m[0],t.channel).get('clear_result')=='success':t.cleared=True
            else:
                st.anomalies.append(f'Q4 ch={t.channel}: MEC<=20 clear failed')
                directional_fallback_clear(api,t,st)
        else:
            directional_fallback_clear(api,t,st)
        pending.remove(t)
    return st
