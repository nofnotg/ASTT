from __future__ import annotations


def evaluate_source_candidate_gate_v559(candidate: dict | None, snapshot: dict | None = None) -> dict:
    if not candidate:
        return {"decision": "WAIT", "gate_pass": False, "reasons": ["NO_CANDIDATE"], "real_order_enabled": False}
    reasons = []
    if candidate.get("real_order_enabled") is not False:
        reasons.append("REAL_ORDER_NOT_ALLOWED")
    if float(candidate.get("expected_target_pct", 0.0)) < 0.30:
        reasons.append("TARGET_TOO_SMALL")
    decision = "ENTER" if not reasons else "WAIT"
    return {"decision": decision, "gate_pass": decision == "ENTER", "reasons": reasons, "real_order_enabled": False}
