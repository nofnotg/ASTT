from __future__ import annotations


ALLOWED_LIVE_OPINIONS = {"LIVE_NOT_ALLOWED", "PAPER_MORE_REQUIRED"}


def enforce_timing_review_schema(row: dict) -> dict:
    safe = {
        "live_readiness_opinion": row.get("live_readiness_opinion", "LIVE_NOT_ALLOWED"),
        "primary_problem": row.get("primary_problem", "DATA_INSUFFICIENT"),
        "timing_assessment": row.get("timing_assessment", "NOT_READY"),
        "recommended_event_types": list(row.get("recommended_event_types", [])),
        "event_types_to_pause": list(row.get("event_types_to_pause", [])),
        "state_transition_findings": list(row.get("state_transition_findings", [])),
        "next_experiments": list(row.get("next_experiments", [])),
        "risk_flags": list(row.get("risk_flags", [])),
        "config_proposals": list(row.get("config_proposals", [])),
        "auto_apply_allowed": False,
        "live_order_allowed": False,
        "active": False,
        "human_approved": False,
    }
    if safe["live_readiness_opinion"] not in ALLOWED_LIVE_OPINIONS:
        safe["live_readiness_opinion"] = "LIVE_NOT_ALLOWED"
    return safe
