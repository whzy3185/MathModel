"""Run the frozen Q3/Q4 policy against the official localhost simulator.

This entry point does not access hidden case truth. It only uses the four documented HTTP+JSON
interfaces through SimulatorClient. Run it on the same computer as the official simulator after
the GUI reports that the robot interface is ready.
"""
from __future__ import annotations

import argparse
import json
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from q3_policy import run_q3_policy
from q4_policy import run_q4_policy
from simulator_client import SimulatorClient, SimulatorProtocolError


class DeadlineGuardAPI:
    """Abort new actions before the real-time deadline, leaving a margin for /exit."""

    def __init__(self, client: SimulatorClient, margin_s: float = 8.0):
        self.client = client
        self.margin_s = margin_s

    def _guard(self):
        left = self.client.real_seconds_left(self.margin_s)
        if left is not None and left <= 0:
            raise TimeoutError("real-time safety margin reached before next action")

    def measure(self, x: float, y: float, channel: int):
        self._guard()
        return self.client.measure(x, y, channel)

    def clear(self, x: float, y: float, channel: int):
        self._guard()
        return self.client.clear(x, y, channel)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", type=int, choices=(3, 4), required=True)
    ap.add_argument("--robot-id", required=True, help="current official team/robot id")
    ap.add_argument("--base-url", default="http://127.0.0.1:2026")
    ap.add_argument("--case-code", default="UNKNOWN", help="copy the case code shown by the simulator UI")
    ap.add_argument("--out-dir", default="coder/results/official_runs")
    ap.add_argument("--real-margin-s", type=float, default=8.0)
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.out_dir) / f"q{args.question}_{stamp}_{args.case_code}"
    run_dir.mkdir(parents=True, exist_ok=True)
    action_log = run_dir / "robot_actions.jsonl"

    client = SimulatorClient(
        robot_id=args.robot_id,
        base_url=args.base_url,
        log_path=str(action_log),
    )
    wall_start = time.monotonic()
    exit_response = None
    error = None
    stats = None
    enter_response = None

    try:
        enter_response = client.enter()
        guarded = DeadlineGuardAPI(client, args.real_margin_s)
        if args.question == 3:
            stats = run_q3_policy(
                guarded,
                defer_localization_until_scan_complete=True,
                opportunistic_until_localized=True,
            )
        else:
            stats = run_q4_policy(guarded, spacing=1000.0)
    except (SimulatorProtocolError, TimeoutError, OSError, ValueError) as exc:
        error = repr(exc)
    finally:
        # /exit is attempted only while the client still believes time remains. If the simulator
        # has already closed the interface this may fail; that failure is recorded, not hidden.
        try:
            left = client.real_seconds_left(0.5)
            if enter_response is not None and (left is None or left > 0):
                exit_response = client.exit()
        except Exception as exc:  # evidence collection: preserve exact exit failure
            if error is None:
                error = f"exit_failure: {exc!r}"
            else:
                error += f"; exit_failure: {exc!r}"

    wall_elapsed = time.monotonic() - wall_start
    cleared = len(getattr(stats, "cleared_channels", [])) if stats is not None else 0
    virtual_time = float(getattr(stats, "virtual_time_s", client.last_virtual_time_s)) if stats is not None else client.last_virtual_time_s
    summary = {
        "question": args.question,
        "case_code": args.case_code,
        "robot_id": args.robot_id,
        "base_url": args.base_url,
        "enter_response": enter_response,
        "exit_response": exit_response,
        "cleared_source_count": cleared,
        "virtual_time_s": virtual_time,
        "average_localize_clear_time_s": (virtual_time / cleared if cleared else None),
        "program_wall_time_s_local": wall_elapsed,
        "measure_calls": getattr(stats, "measure_calls", None),
        "clear_calls": getattr(stats, "clear_calls", None),
        "policy_anomalies": getattr(stats, "anomalies", None),
        "runner_error": error,
        "action_log": str(action_log),
        "evidence_note": "Formal paper values must be cross-checked with the official simulator UI/encrypted log; this file is the robot-side evidence record.",
    }
    (run_dir / "run_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
