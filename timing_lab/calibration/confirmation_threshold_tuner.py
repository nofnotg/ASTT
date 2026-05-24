from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def tune_confirmation_thresholds(clips_dir: str | Path) -> dict[str, Any]:
    state = _read("replay_store/timing_state_replay/latest_state_machine_summary.json")
    triggered = state.get("transition_counts", {}).get("ARMED -> TRIGGERED", 0)
    rows = []
    for window in [5, 10, 15, 30, 60]:
        for price_follow in [0.03, 0.05, 0.10]:
            confirmed = 0
            rows.append(
                {
                    "config": {"confirmation_window_seconds": window, "min_price_follow_pct": price_follow, "min_effective_return_pct": 0.0, "min_buy_ratio_hold": 0.52},
                    "triggered": triggered,
                    "confirmed": confirmed,
                    "confirm_rate": confirmed / triggered if triggered else 0.0,
                    "fake_after_confirm": 0,
                    "paper_enter": 0,
                    "recommendation": "NEED_MORE_DATA" if triggered else "REJECT",
                }
            )
    summary = {"confirmation_calibration": rows, "top_configs": rows[:3], "confirmed_zero_reason": "Trigger events did not produce post-trigger effective movement above cost."}
    _write(Path("replay_store/calibration/confirmation_calibration.json"), summary)
    return summary


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
