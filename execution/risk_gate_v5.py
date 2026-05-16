from __future__ import annotations


def evaluate_risk_gate_v5(candidate: dict, minimum_rr: float = 1.2) -> dict:
    veto_reasons: list[str] = []
    warnings: list[str] = []
    if candidate.get("regime", {}).get("regime") == "BTC_SHOCK" or not candidate.get("regime", {}).get("long_allowed", True):
        veto_reasons.append("BTC_SHOCK_OR_RISK_OFF")
    if float(candidate.get("risk_reward", 0.0)) < minimum_rr:
        veto_reasons.append("risk_reward_below_minimum")
    if float(candidate.get("target_space_pct", 0.0)) < 0.6:
        veto_reasons.append("target_space_too_small")
    if float(candidate.get("spread_pct", 0.0)) > 0.25:
        veto_reasons.append("spread_too_wide")
    if candidate.get("data_quality") == "LOW":
        veto_reasons.append("data_quality_low")
    if candidate.get("daily_loss_limit_reached", False):
        veto_reasons.append("daily_loss_limit_reached")
    if candidate.get("weekly_loss_limit_reached", False):
        veto_reasons.append("weekly_loss_limit_reached")
    if int(candidate.get("consecutive_losses", 0)) > 2:
        veto_reasons.append("consecutive_losses_exceeded")
    if float(candidate.get("distance_to_resistance_pct", 999.0)) < 0.4:
        warnings.append("entry_close_to_resistance")
    score = 100.0 - len(veto_reasons) * 24 - len(warnings) * 8
    decision = "REJECT" if veto_reasons else "WARN" if warnings or score < 75 else "PASS"
    return {"risk_decision": decision, "risk_score": max(0.0, min(100.0, score)), "veto": bool(veto_reasons), "veto_reasons": veto_reasons, "warnings": warnings}
