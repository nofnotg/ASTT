from __future__ import annotations

from scenario_telemetry.v688_common import top_counts


def analyze_no_trade_reasons(forward_events: list[dict]) -> dict:
    reasons = [event.get("primary_block_reason") for event in forward_events if event.get("entry_decision") != "ENTER"]
    return {"top_reasons": top_counts(reasons), "enter_count": len([e for e in forward_events if e.get("entry_decision") == "ENTER"]), "candidate_count": len(forward_events)}
