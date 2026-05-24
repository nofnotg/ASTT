from __future__ import annotations

from collections import Counter
from typing import Any


def build_timing_metrics(events: list[dict[str, Any]], clips: list[dict[str, Any]], labels: list[dict[str, Any]], state_summary: dict[str, Any], paper_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    paper_summary = paper_summary or {}
    label_counts = Counter(row.get("label", "UNKNOWN") for row in labels)
    entry_window_count = label_counts.get("ENTRY_WINDOW", 0)
    event_count = len(events)
    return {
        "event_count": event_count,
        "clip_count": len(clips),
        "entry_window_count": entry_window_count,
        "entry_window_rate": entry_window_count / len(clips) if clips else 0.0,
        "state_transition_counts": state_summary.get("transition_counts", {}),
        "abort_reason_counts": state_summary.get("abort_reason_counts", {}),
        "too_early_count": label_counts.get("TOO_EARLY", 0),
        "too_late_count": label_counts.get("TOO_LATE", 0),
        "fake_signal_count": label_counts.get("FAKE_SIGNAL", 0),
        "liquidity_trap_count": label_counts.get("LIQUIDITY_TRAP", 0),
        "spread_trap_count": label_counts.get("SPREAD_TRAP", 0),
        "paper_trade_count": paper_summary.get("paper_enter_count", 0),
        "realistic_1_pnl_evaluable": paper_summary.get("pnl_evaluable", False),
    }
