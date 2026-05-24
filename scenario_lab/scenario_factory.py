from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from replay_lab.paths import REPLAY_STORE_DIR


SCENARIO_TYPES = [
    "UPTREND",
    "DOWNTREND",
    "BTC_CHOP",
    "ALT_ROTATION",
    "VOLUME_SURGE",
    "FAKE_RANK_SURGE",
    "NO_FOLLOW_THROUGH",
    "BREAKOUT_FAIL",
    "PULLBACK_SUCCESS",
]


def build_scenarios_v5r3() -> dict[str, Any]:
    setup = _read(REPLAY_STORE_DIR / "setup_candidates" / "latest_setup_candidate_summary.json")
    fake = _read(REPLAY_STORE_DIR / "fake_signal" / "fake_signal_decomposition.json")
    candidates = setup.get("candidates", [])
    scenarios = []
    for row in candidates:
        scenarios.append({**row, "scenario_type": _scenario_type(row), "source": "SETUP_CANDIDATE"})
    for row in fake.get("rows", [])[:80]:
        scenarios.append({
            "candidate_id": f"{row.get('clip_id')}_fake_replay",
            "clip_id": row.get("clip_id"),
            "event_id": row.get("event_id"),
            "market": row.get("market"),
            "event_type": row.get("event_type"),
            "setup_type": row.get("fake_subtype"),
            "setup_score": 20,
            "setup_grade": "C",
            "scenario_type": "FAKE_RANK_SURGE" if row.get("fake_subtype") == "RANK_SURGE_FAKE" else "NO_FOLLOW_THROUGH",
            "source": "V5R2_FAKE_SIGNAL",
            "real_order_enabled": False,
        })
    counts = Counter(row["scenario_type"] for row in scenarios)
    summary = {
        "schema_version": "v5r3",
        "scenario_count": len(scenarios),
        "scenario_counts": dict(counts),
        "by_scenario_type": dict(counts),
        "scenarios": scenarios,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(REPLAY_STORE_DIR / "scenarios" / "latest_scenario_set.json", summary)
    _write(
        Path("docs/reports/latest_scenario_replay_summary.json"),
        {
            "schema_version": "v5r3",
            "scenario_count": len(scenarios),
            "scenario_counts": dict(counts),
            "by_scenario_type": dict(counts),
            "real_order_enabled": False,
        },
    )
    return summary


def _scenario_type(row: dict[str, Any]) -> str:
    setup_type = row.get("setup_type")
    event_type = row.get("event_type")
    if setup_type == "LEADER_ROTATION_SURGE":
        return "ALT_ROTATION"
    if setup_type == "VWAP_RECLAIM_WITH_VOLUME":
        return "VOLUME_SURGE"
    if setup_type == "RANGE_BREAKOUT":
        return "BREAKOUT_FAIL"
    if setup_type == "PULLBACK_RECLAIM":
        return "PULLBACK_SUCCESS"
    if event_type == "MARKET_RANK_SURGE":
        return "FAKE_RANK_SURGE"
    return "BTC_CHOP"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
