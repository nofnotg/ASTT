from __future__ import annotations

from active_analysis.recommendation_scoring import recommendation


def experiments_from_triggers(pipeline: dict, no_trade: dict, delta: dict, route_state: dict) -> list[dict]:
    rows = []
    if route_state.get("mismatch_warning"):
        rows.append(recommendation("route_state_fix", "Route Display Mismatch Trigger", "HIGH", 0.9, "dashboard route state fix", allowed_action="DASHBOARD_WARNING"))
    if pipeline.get("forward_collector_stale") or pipeline.get("ledger_update_stale"):
        rows.append(recommendation("forward_pipeline_health_fix", "Pipeline Stale Trigger", "HIGH", 0.85, "separate candidate log from ledger and monitor stale state", allowed_action="DASHBOARD_WARNING"))
    if no_trade.get("candidate_count", 0) > 0 and no_trade.get("enter_count", 0) == 0:
        rows.append(recommendation("skip_reason_audit", "Candidate Starvation Trigger", "MEDIUM", 0.75, "audit repeated wait reasons such as MICRO_STATE_WEAK", allowed_action="SHADOW_EXPERIMENT"))
    if delta.get("shadow_outperforming"):
        rows.append(recommendation("shadow_promotion_review", "Shadow Outperformance Trigger", "MEDIUM", 0.6, "manual review of outperforming shadow", allowed_action="MANUAL_REVIEW"))
    if not rows:
        rows.append(recommendation("paper_more_required", "Baseline Monitoring", "LOW", 0.5, "continue paper observation", allowed_action="REPORT_ONLY"))
    return rows
