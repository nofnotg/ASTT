from __future__ import annotations

ALLOWED_READINESS = {"LIVE_NOT_ALLOWED", "PAPER_MORE_REQUIRED"}
FORBIDDEN_TERMS = ["LIVE_READY", "MICRO_LIVE_READY", "real_order_enabled true", "enable live trading", "disable stop loss", "remove stop loss", "auto apply"]


def validate_and_sanitize_llm_output(data: dict) -> dict:
    if data.get("live_readiness_opinion") not in ALLOWED_READINESS:
        raise ValueError("invalid_live_readiness_opinion")
    safe = {
        "summary": str(data.get("summary", "")),
        "live_readiness_opinion": data.get("live_readiness_opinion", "LIVE_NOT_ALLOWED"),
        "primary_problem": str(data.get("primary_problem", "UNKNOWN")),
        "root_cause_hypotheses": [str(v) for v in data.get("root_cause_hypotheses", [])],
        "next_experiments": [str(v) for v in data.get("next_experiments", [])],
        "risk_flags": [str(v) for v in data.get("risk_flags", [])],
        "config_proposals": [],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
    text = str(data)
    if any(term.lower() in text.lower() for term in FORBIDDEN_TERMS):
        safe["risk_flags"].append("LLM_UNSAFE_PROPOSAL_REJECTED")
    for proposal in data.get("config_proposals", []):
        p = dict(proposal)
        if p.get("active") is True:
            safe["risk_flags"].append("LLM_ACTIVE_CONFIG_BLOCKED")
        if p.get("human_approved") is True:
            safe["risk_flags"].append("LLM_HUMAN_APPROVAL_BLOCKED")
        p["active"] = False
        p["human_approved"] = False
        p["requires_validation"] = True
        safe["config_proposals"].append(p)
    return safe
