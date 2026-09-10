"""Aggregate robot-side official-run summaries into the problem Table-1 layout.

The encrypted simulator logs are intentionally not parsed or renamed here. Preserve their original
filenames in coder/results/formal_logs and cross-check the generated CSV against the simulator UI.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--question", type=int, choices=(3, 4), required=True)
    ap.add_argument("--runs-dir", default="coder/results/official_runs")
    ap.add_argument("--output", default=None)
    args = ap.parse_args()

    root = Path(args.runs_dir)
    rows = []
    for p in sorted(root.glob(f"q{args.question}_*/run_summary.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        rows.append({
            "测试案例编码": rec.get("case_code", "UNKNOWN"),
            "清除干扰源个数": rec.get("cleared_source_count"),
            "平均定位清除时间": rec.get("average_localize_clear_time_s"),
            "程序运行时间": rec.get("program_wall_time_s_local"),
            "robot_summary_path": str(p),
            "needs_official_crosscheck": True,
        })

    out = Path(args.output or f"coder/results/q{args.question}_formal_table_robot_side.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["测试案例编码", "清除干扰源个数", "平均定位清除时间", "程序运行时间", "robot_summary_path", "needs_official_crosscheck"]
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
