"""Official-simulator HTTP+JSON client following Attachment 2.

No search strategy is embedded here; this module only enforces protocol, serial actions,
idempotent retries, deadline awareness, and machine-readable logs.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SimulatorProtocolError(RuntimeError):
    pass


@dataclass
class ActionResult:
    path: str
    payload: Dict[str, Any]
    response: Dict[str, Any]
    http_status: int


class SimulatorClient:
    def __init__(
        self,
        robot_id: str,
        base_url: str = "http://127.0.0.1:2026",
        arena_id: str = "default",
        timeout_s: float = 5.0,
        log_path: str = "robot_actions.jsonl",
    ):
        self.robot_id = robot_id
        self.base_url = base_url.rstrip("/")
        self.arena_id = arena_id
        self.timeout_s = timeout_s
        self.log_path = Path(log_path)
        self._seq = 0
        self.enter_monotonic: Optional[float] = None
        self.remaining_real_duration_s: Optional[float] = None
        self.last_virtual_time_s = 0.0

    def _new_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq}-{uuid.uuid4().hex[:10]}"

    def _base(self, request_id: str) -> Dict[str, Any]:
        return {"arena_id": self.arena_id, "robot_id": self.robot_id, "request_id": request_id}

    def _write_log(self, rec: Dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")

    def _post_exact(self, path: str, payload: Dict[str, Any]) -> ActionResult:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        req = Request(
            self.base_url + path,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        t0 = time.time()
        try:
            with urlopen(req, timeout=self.timeout_s) as r:
                status = int(getattr(r, "status", 200))
                raw = r.read().decode("utf-8")
        except HTTPError as e:
            status = e.code
            raw = e.read().decode("utf-8", errors="replace")
        response = json.loads(raw)
        rec = {
            "wall_time": t0,
            "path": path,
            "payload": payload,
            "http_status": status,
            "response": response,
        }
        self._write_log(rec)
        if response.get("accepted") is True:
            self.last_virtual_time_s = float(response.get("virtual_time_s", self.last_virtual_time_s))
        return ActionResult(path, payload, response, status)

    def _post_with_idempotent_retry(
        self, path: str, payload: Dict[str, Any], retries: int = 2, retry_delay_s: float = 0.15
    ) -> ActionResult:
        # Crucial: retries use byte-equivalent semantic action and the SAME request_id.
        last_exc: Optional[BaseException] = None
        for k in range(retries + 1):
            try:
                result = self._post_exact(path, payload)
                if result.http_status != 200:
                    raise SimulatorProtocolError(f"HTTP {result.http_status}: {result.response}")
                if result.response.get("accepted") is not True:
                    raise SimulatorProtocolError(f"accepted=false: {result.response}")
                return result
            except (URLError, TimeoutError, ConnectionError) as e:
                last_exc = e
                self._write_log({"wall_time": time.time(), "path": path, "payload": payload, "network_error": repr(e), "retry": k})
                if k < retries:
                    time.sleep(retry_delay_s)
        raise SimulatorProtocolError(f"Network failure after idempotent retries: {last_exc!r}")

    def enter(self) -> Dict[str, Any]:
        payload = self._base(self._new_id("enter"))
        r = self._post_with_idempotent_retry("/enter", payload).response
        self.enter_monotonic = time.monotonic()
        self.remaining_real_duration_s = float(r["remaining_real_duration_s"])
        return r

    def measure(self, x: float, y: float, channel: int) -> Dict[str, Any]:
        payload = self._base(self._new_id("measure"))
        payload["position"] = {"x": float(x), "y": float(y)}
        payload["channel"] = int(channel)
        return self._post_with_idempotent_retry("/measure", payload).response

    def clear(self, x: float, y: float, channel: int) -> Dict[str, Any]:
        payload = self._base(self._new_id("clear"))
        payload["position"] = {"x": float(x), "y": float(y)}
        payload["channel"] = int(channel)
        return self._post_with_idempotent_retry("/clear", payload).response

    def exit(self) -> Dict[str, Any]:
        payload = self._base(self._new_id("exit"))
        return self._post_with_idempotent_retry("/exit", payload).response

    def real_seconds_left(self, safety_margin_s: float = 0.0) -> Optional[float]:
        if self.enter_monotonic is None or self.remaining_real_duration_s is None:
            return None
        used = time.monotonic() - self.enter_monotonic
        return self.remaining_real_duration_s - used - safety_margin_s
