from __future__ import annotations


def evaluate_tradable_candidate_gate_v5510(candidate: dict | None) -> dict:
    if not candidate:
        return {"decision": "WAIT", "gate_pass": False, "reasons": ["NO_CANDIDATE"], "real_order_enabled": False}
    reasons = []
    if candidate.get("real_order_enabled") is not False:
        reasons.append("REAL_ORDER_NOT_ALLOWED")
    if not candidate.get("tradable_prefilter_pass", False):
        reasons.append("TRADABLE_PREFILTER_FAIL")
    if float(candidate.get("effective_return_pct", 0.0) or 0.0) <= 0:
        reasons.append("EFFECTIVE_RETURN_NON_POSITIVE")
    if float(candidate.get("spread_pct", 999.0) or 999.0) > 0.20:
        reasons.append("SPREAD_TOO_WIDE")
    if float(candidate.get("depth_3_level_krw", 0.0) or 0.0) < 1_000_000:
        reasons.append("DEPTH_INSUFFICIENT")
    decision = "ENTER" if not reasons else "WAIT"
    return {"decision": decision, "gate_pass": decision == "ENTER", "reasons": reasons, "real_order_enabled": False}
