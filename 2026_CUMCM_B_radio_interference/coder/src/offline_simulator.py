"""Offline development simulator matching the published physical/timing rules.

This is NOT the official simulator and never generates evidence for formal-test claims.
Its purpose is deterministic unit/integration testing before running localhost:2026.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import atan2, cos, degrees, hypot, radians, sin
from typing import Dict, Iterable, List, Optional, Tuple

Point = Tuple[float, float]


def wrap_deg(x: float) -> float:
    return x % 360.0


def signed_angle_deg(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


@dataclass
class Source:
    channel: int
    x: float
    y: float
    receive_radius: float
    direction_deg: Optional[float] = None  # None => omni
    cleared: bool = False


class OfflineSimulator:
    def __init__(self, sources: Iterable[Source], seed: int = 20260910, error_mode: str = "hash_uniform"):
        self.sources: Dict[int, Source] = {s.channel: s for s in sources}
        self.seed = seed
        self.error_mode = error_mode
        self.position: Point = (0.0, 0.0)
        self.current_channel = 1
        self.virtual_time_s = 0.0
        self.entered = False
        self.exited = False

    def enter(self):
        if self.entered or self.exited:
            return {"accepted": False, "virtual_time_s": 0}
        self.entered = True
        return {
            "accepted": True,
            "virtual_time_s": self.virtual_time_s,
            "max_virtual_duration_s": 360000,
            "max_real_duration_s": 1200,
            "remaining_real_duration_s": 1200,
        }

    def _move(self, p: Point) -> None:
        self.virtual_time_s += hypot(p[0] - self.position[0], p[1] - self.position[1]) / 5.0
        self.position = p

    def _source_visible(self, s: Source, p: Point) -> bool:
        d = hypot(p[0] - s.x, p[1] - s.y)
        if d > s.receive_radius + 1e-9:
            return False
        if s.direction_deg is None:
            return True
        receiver_bearing = wrap_deg(degrees(atan2(p[1] - s.y, p[0] - s.x)))
        return abs(signed_angle_deg(receiver_bearing, s.direction_deg)) <= 90.0 + 1e-12

    def _fixed_local_error(self, channel: int, p: Point) -> float:
        # Same channel+same location => same error.  1 cm quantization is only for the
        # offline fixture and is not asserted about the official simulator.
        key = f"{self.seed}|{channel}|{round(p[0],2)}|{round(p[1],2)}".encode()
        digest = sha256(key).digest()
        if self.error_mode == "plus_one":
            return 1.0
        if self.error_mode == "minus_one":
            return -1.0
        if self.error_mode == "endpoint_hash":
            return 1.0 if (digest[0] & 1) else -1.0
        if self.error_mode != "hash_uniform":
            raise ValueError(f"unknown error_mode={self.error_mode}")
        v = int.from_bytes(digest[:8], "big") / 2**64
        return 2.0 * v - 1.0

    def measure(self, x: float, y: float, channel: int):
        if not self.entered or self.exited:
            return {"accepted": False, "virtual_time_s": 0}
        p = (float(x), float(y))
        self._move(p)
        if int(channel) != self.current_channel:
            self.virtual_time_s += 1.0
            self.current_channel = int(channel)
        self.virtual_time_s += 5.0
        s = self.sources.get(int(channel))
        if s is None or s.cleared or not self._source_visible(s, p):
            return {"accepted": True, "virtual_time_s": self.virtual_time_s, "measure_result": "no_signal"}
        d = hypot(p[0] - s.x, p[1] - s.y)
        if d <= 5.0 + 1e-12:
            return {"accepted": True, "virtual_time_s": self.virtual_time_s, "measure_result": "near"}
        true_bearing = wrap_deg(degrees(atan2(s.y - p[1], s.x - p[0])))
        measured = wrap_deg(true_bearing + self._fixed_local_error(channel, p))
        return {
            "accepted": True,
            "virtual_time_s": self.virtual_time_s,
            "measure_result": "direction",
            "svd_deg": round(measured, 2),
        }

    def clear(self, x: float, y: float, channel: int):
        if not self.entered or self.exited:
            return {"accepted": False, "virtual_time_s": 0}
        p = (float(x), float(y))
        self._move(p)
        self.virtual_time_s += 3.0
        s = self.sources.get(int(channel))
        if s is not None and not s.cleared and hypot(p[0] - s.x, p[1] - s.y) <= 20.0 + 1e-12:
            s.cleared = True
            self.virtual_time_s += 2.0
            return {"accepted": True, "virtual_time_s": self.virtual_time_s, "clear_result": "success"}
        return {"accepted": True, "virtual_time_s": self.virtual_time_s, "clear_result": "no_target_in_range"}

    def exit(self):
        self.exited = True
        return {"accepted": True, "virtual_time_s": self.virtual_time_s, "exit_reason": "user_exit"}
