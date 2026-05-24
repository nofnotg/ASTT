from __future__ import annotations


def size_signal_strength(candidate: dict, policy: dict | None = None) -> dict:
    policy = policy or {"initial_cash_krw": 500000}
    score = float(candidate.get("micro_strength_score", candidate.get("score", 0.0)) or 0.0)
    cost_ratio = candidate.get("cost_to_target_ratio")
    risk_flags = list(candidate.get("risk_flags", []))
    if candidate.get("entry_decision") in {"WAIT", "CANCEL"} or candidate.get("research_only"):
        grade, pct = "C", 0.0
        risk_flags.append("NO_REAL_ENTRY")
    elif cost_ratio is not None and float(cost_ratio) >= 0.3:
        grade, pct = "C", 0.0
        risk_flags.append("COST_TO_TARGET_TOO_HIGH")
    elif score >= 80:
        grade, pct = "S", 0.8
    elif score >= 65:
        grade, pct = "A", 0.5
    elif score >= 50:
        grade, pct = "B", 0.15
    else:
        grade, pct = "C", 0.0
    allocation_krw = float(policy.get("initial_cash_krw", 500000)) * pct
    return {
        "signal_grade": grade,
        "allocation_pct": pct,
        "allocation_krw": allocation_krw,
        "reason": [f"score={score}"],
        "risk_flags": risk_flags,
    }
