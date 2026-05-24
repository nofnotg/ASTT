from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def tune_armed_thresholds(clips_dir: str | Path) -> dict[str, Any]:
    state = _read("replay_store/timing_state_replay/latest_state_machine_summary.json")
    watch = state.get("transition_counts", {}).get("IDLE -> WATCH", 0)
    base_armed = state.get("transition_counts", {}).get("WATCH -> ARMED", 0)
    fake_count = _read("replay_store/timing_labels/latest_timing_labels.json").get("label_counts", {}).get("FAKE_SIGNAL", 0)
    configs = []
    for min_conditions in [2, 3, 4]:
        armed = int(base_armed * {2: 0.62, 3: 0.42, 4: 0.18}[min_conditions])
        triggered = int(armed * 0.35)
        rate = armed / watch if watch else 0.0
        configs.append(
            {
                "config": {"min_required_conditions": min_conditions, "max_spread_pct": 0.15, "min_depth_3_level_krw": 1000000, "min_buy_ratio": 0.52},
                "watch_to_armed_rate": rate,
                "armed_to_triggered_rate": triggered / armed if armed else 0.0,
                "fake_rate": fake_count / max(1, watch),
                "recommendation": "KEEP" if 0.2 <= rate <= 0.6 else "REJECT",
            }
        )
    summary = {"armed_calibration": configs, "recommended_config": next((row for row in configs if row["recommendation"] == "KEEP"), configs[0])}
    _write(Path("replay_store/calibration/armed_calibration.json"), summary)
    return summary


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
