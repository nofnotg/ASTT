from __future__ import annotations

from datetime import date, datetime
from typing import Any


def analyze_forward_pipeline(forward_summary: dict[str, Any], forward_events: list[dict[str, Any]]) -> dict[str, Any]:
    timestamp = None
    source = forward_summary.get("source_session", {}) if isinstance(forward_summary.get("source_session"), dict) else {}
    raw = forward_summary.get("ended_at") or source.get("ended_at") or source.get("started_at")
    if raw:
        try:
            timestamp = datetime.fromisoformat(str(raw)).date()
        except ValueError:
            timestamp = None
    stale = timestamp is None or (date.today() - timestamp).days > 1
    return {
        "forward_collector_stale": stale,
        "candidate_log_stale": stale or not forward_events,
        "decision_loop_stale": stale,
        "ledger_update_stale": True,
        "latest_forward_date": timestamp.isoformat() if timestamp else None,
        "candidate_count": len(forward_events),
        "status": "STALE_OR_LEDGER_GAP" if stale or not forward_events else "FORWARD_CANDIDATE_LOG_OK_LEDGER_SEPARATE",
    }
