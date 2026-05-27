from __future__ import annotations

from typing import Any


def build_v67_rejection_report(summary: dict[str, Any]) -> dict[str, Any]:
    rejected = []
    kept = []
    for row in summary.get("scenarios", []):
        scenario = row.get("scenario")
        decision = row.get("decision")
        if scenario == "CONTROL_EXISTING":
            continue
        if decision in {"GLOBAL_BTCD_FILTER_VALIDATED", "GLOBAL_BTCD_RELATIVE_STRENGTH_CANDIDATE", "BEAR_REGIME_CANDIDATE"}:
            kept.append({"scenario": scenario, "keep_reason": decision, "forward_candidate": decision != "GLOBAL_BTCD_FILTER_VALIDATED"})
        else:
            rejected.append({"scenario": scenario, "reject_reason": decision or "BELOW_CRITERIA"})
    return {
        "schema_version": "v67_global_btcd_rejected_scenarios_v1",
        "rejected_scenarios": rejected,
        "kept_candidates": kept,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
