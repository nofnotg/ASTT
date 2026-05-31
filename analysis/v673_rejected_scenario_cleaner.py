from __future__ import annotations

from typing import Any


KEEP_DECISIONS = {
    "DOMINANCE_FILTER_VALIDATED",
    "ROLLING_BTCDOM_CANDIDATE",
    "BALANCED_BTCDOM_CANDIDATE",
    "POLICY_BLEND_BTCDOM_CANDIDATE",
    "BEAR_AGENT_CANDIDATE",
    "SCENARIO_AGENT_ROUTER_CANDIDATE",
}


def build_v673_rejection_report(summary: dict[str, Any]) -> dict[str, Any]:
    rejected: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for row in summary.get("scenarios", []):
        scenario = row.get("scenario")
        if scenario in {"CONTROL_EXISTING", "POLICY_BLEND_CONTROL"}:
            continue
        decision = row.get("decision") or "UNDER_THRESHOLD"
        if decision in KEEP_DECISIONS:
            kept.append({"scenario": scenario, "keep_reason": decision, "forward_candidate": True})
        else:
            rejected.append({"scenario": scenario, "reject_reason": decision})
    return {
        "schema_version": "v673_rejected_scenarios_v1",
        "rejected_scenarios": rejected,
        "kept_candidates": kept,
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
