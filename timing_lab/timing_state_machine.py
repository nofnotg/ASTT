from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from timing_lab.event_clip_store import read_jsonl
from timing_lab.timing_state_schema import TimingStateSnapshot


class EntryTimingStateMachine:
    def __init__(self):
        self.state = "IDLE"
        self.transitions: list[tuple[str, str]] = []
        self.abort_reasons: list[str] = []

    def apply(self, event: dict[str, Any], features: dict[str, Any]) -> TimingStateSnapshot:
        self._transition("WATCH")
        if features.get("spread_stable") and features.get("depth_sufficient") and not features.get("btc_negative_shock"):
            self._transition("ARMED")
        else:
            return self._abort(event, features)
        if features.get("buy_trade_ratio", 0) >= 0.55 and features.get("volume_burst"):
            self._transition("TRIGGERED")
        else:
            return self._abort(event, {**features, "abort_reason": "FOLLOW_THROUGH_FAIL"})
        if features.get("follow_through"):
            self._transition("CONFIRMED")
        else:
            return self._abort(event, {**features, "abort_reason": "FOLLOW_THROUGH_FAIL"})
        if features.get("allocator_grade") in {"B", "A", "S"} and features.get("entry_window_exists"):
            self._transition("ENTER")
        else:
            self._abort(event, {**features, "abort_reason": "TIMING_EXPIRED"})
        return self.snapshot(event, features)

    def snapshot(self, event: dict[str, Any], features: dict[str, Any]) -> TimingStateSnapshot:
        return TimingStateSnapshot(event.get("market", ""), event.get("event_id", ""), self.state, int(event.get("event_time_ms", 0)), 0, features, [], self.abort_reasons)

    def _transition(self, next_state: str) -> None:
        self.transitions.append((self.state, next_state))
        self.state = next_state

    def _abort(self, event: dict[str, Any], features: dict[str, Any]) -> TimingStateSnapshot:
        reason = features.get("abort_reason")
        if not reason:
            reason = "SPREAD_TOO_WIDE" if not features.get("spread_stable") else "DEPTH_INSUFFICIENT"
        self.abort_reasons.append(reason)
        self._transition("ABORT")
        return self.snapshot(event, features)


def validate_state_machine_for_clips(clips_dir: str | Path, labels: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    label_by_clip = {row["clip_id"]: row for row in labels or []}
    transitions = Counter()
    final_states = Counter()
    abort_reasons = Counter()
    states: list[dict[str, Any]] = []
    for meta_path in Path(clips_dir).glob("*/*/clip_meta.json"):
        meta = __import__("json").loads(meta_path.read_text(encoding="utf-8"))
        if str(meta.get("market", "")).endswith("TEST"):
            continue
        trades = read_jsonl(meta_path.parent / "trades.jsonl")
        orderbooks = read_jsonl(meta_path.parent / "orderbooks.jsonl")
        label = label_by_clip.get(meta["clip_id"], {})
        features = _clip_features(trades, orderbooks, label)
        machine = EntryTimingStateMachine()
        snapshot = machine.apply(meta, features).to_dict()
        states.append(snapshot)
        transitions.update([f"{a} -> {b}" for a, b in machine.transitions])
        final_states.update([snapshot["state"]])
        abort_reasons.update(snapshot.get("abort_reasons", []))
    return {
        "state_count": len(states),
        "states": states,
        "transition_counts": dict(transitions),
        "final_state_counts": dict(final_states),
        "abort_reason_counts": dict(abort_reasons),
    }


def _clip_features(trades: list[dict[str, Any]], orderbooks: list[dict[str, Any]], label: dict[str, Any]) -> dict[str, Any]:
    buy_ratio = sum(1 for row in trades if row.get("ask_bid") == "BID") / len(trades) if trades else 0.0
    return {
        "spread_stable": bool(orderbooks),
        "depth_sufficient": bool(orderbooks),
        "btc_negative_shock": False,
        "buy_trade_ratio": buy_ratio,
        "volume_burst": len(trades) >= 3,
        "follow_through": label.get("label") == "ENTRY_WINDOW",
        "entry_window_exists": label.get("label") == "ENTRY_WINDOW",
        "allocator_grade": "B" if label.get("tradable_with_500k") else "C",
    }
