from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


EVENT_TYPES = ["VOLUME_SPIKE", "ORDERFLOW_SHIFT", "SPREAD_CONTRACTION", "DEPTH_RECOVERY", "RANGE_TOUCH", "BREAKOUT_PRESSURE", "BTC_SHOCK", "MARKET_RANK_SURGE"]


def score_event_types(clips_dir: str | Path) -> dict[str, Any]:
    timing = _read("docs/reports/latest_timing_lab_summary.json")
    labels = _read("replay_store/timing_labels/latest_timing_labels.json").get("labels", [])
    states = _read("replay_store/timing_state_replay/latest_state_machine_summary.json").get("states", [])
    events = timing.get("events_by_type", {})
    fake_by_type = Counter(_event_type(row.get("event_id", "")) for row in labels if row.get("label") == "FAKE_SIGNAL")
    no_trade_by_type = Counter(_event_type(row.get("event_id", "")) for row in labels if row.get("label") == "NO_TRADE")
    triggered_by_type = Counter(_event_type(row.get("event_id", "")) for row in states if row.get("state") == "ABORT" and row.get("evidence", {}).get("volume_burst"))
    confirmed_by_type = Counter(_event_type(row.get("event_id", "")) for row in states if row.get("state") in {"CONFIRMED", "ENTER"})
    rows = []
    for event_type in EVENT_TYPES:
        event_count = int(events.get(event_type, 0))
        fake = fake_by_type[event_type]
        no_trade = no_trade_by_type[event_type]
        confirmed = confirmed_by_type[event_type]
        entry = 0
        observed_count = max(event_count, fake + no_trade + entry + confirmed)
        fake_rate = fake / observed_count if observed_count else 0.0
        confirm_rate = confirmed / observed_count if observed_count else 0.0
        decision = "KEEP"
        if observed_count == 0:
            decision = "REMOVE"
        elif fake_rate >= 0.8 or event_type in {"MARKET_RANK_SURGE", "SPREAD_CONTRACTION", "DEPTH_RECOVERY", "BTC_SHOCK"}:
            decision = "PAUSE" if fake_rate >= 0.8 else "TIGHTEN"
        elif confirm_rate == 0:
            decision = "TIGHTEN"
        rows.append(
            {
                "event_type": event_type,
                "event_count": observed_count,
                "raw_event_count": event_count,
                "fake_signal_count": fake,
                "no_trade_count": no_trade,
                "entry_window_count": entry,
                "triggered_count": triggered_by_type[event_type],
                "confirmed_count": confirmed,
                "abort_count": observed_count,
                "follow_through_failure_count": fake,
                "fake_rate": fake_rate,
                "confirmation_rate": confirm_rate,
                "entry_window_rate": 0.0,
                "paper_enter_rate": 0.0,
                "decision": decision,
            }
        )
    summary = {"event_type_scores": rows}
    _write(Path("replay_store/fake_signal/event_type_quality_score.json"), summary)
    return summary


def _event_type(event_id: str) -> str:
    for name in EVENT_TYPES:
        if name in event_id:
            return name
    return "UNKNOWN"


def _read(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
