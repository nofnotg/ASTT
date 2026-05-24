from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from timing_lab.calibration.armed_threshold_tuner import tune_armed_thresholds
from timing_lab.calibration.confirmation_threshold_tuner import tune_confirmation_thresholds


def run_calibration_grid(clips_dir: str | Path) -> dict[str, Any]:
    armed = tune_armed_thresholds(clips_dir)["armed_calibration"]
    confirm = tune_confirmation_thresholds(clips_dir)["confirmation_calibration"][:3]
    rows = []
    for i, a in enumerate(armed):
        c = confirm[min(i, len(confirm) - 1)]
        score = (20 if c["confirmed"] else 0) + (10 if a["recommendation"] == "KEEP" else 0)
        rows.append(
            {
                "grid_id": f"grid_{i+1}",
                "config": {**a["config"], **c["config"]},
                "event_count": _read("docs/reports/latest_timing_lab_summary.json").get("event_count", 0),
                "armed_count": int(a["watch_to_armed_rate"] * max(1, _read("replay_store/timing_state_replay/latest_state_machine_summary.json").get("transition_counts", {}).get("IDLE -> WATCH", 0))),
                "triggered_count": c["triggered"],
                "confirmed_count": c["confirmed"],
                "paper_enter_count": c["paper_enter"],
                "fake_after_confirm_count": c["fake_after_confirm"],
                "estimated_quality_score": score,
                "recommendation": "NEED_MORE_DATA" if a["recommendation"] == "KEEP" else "REJECT",
            }
        )
    summary = {"grid_results": rows, "top_3": sorted(rows, key=lambda row: row["estimated_quality_score"], reverse=True)[:3]}
    _write(Path("replay_store/calibration/calibration_grid.json"), summary)
    return summary


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
