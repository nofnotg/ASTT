from __future__ import annotations

from typing import Any


def build_v672_rejection_report(summary: dict[str, Any]) -> dict[str, Any]:
    rejected = []
    kept = []
    for row in summary.get("scenarios", []):
        scenario = row.get("scenario")
        decision = row.get("decision")
        if scenario == "CONTROL_EXISTING":
            continue
        if decision in {"BTCDOM_INDEX_FILTER_VALIDATED", "BTCDOM_RELATIVE_STRENGTH_CANDIDATE"}:
            kept.append({"scenario": scenario, "keep_reason": decision, "forward_candidate": True})
        else:
            rejected.append({"scenario": scenario, "reject_reason": decision or "UNDER_THRESHOLD"})
    return {
        "schema_version": "v672_btcdom_index_rejected_scenarios_v1",
        "rejected_scenarios": rejected,
        "kept_candidates": kept,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
