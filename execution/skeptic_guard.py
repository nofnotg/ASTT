from __future__ import annotations


def evaluate_skeptic_guard(candidate: dict, mode: str = "BLOCKING", blocking_enabled: bool = True) -> dict:
    reject_reasons: list[str] = []
    warnings: list[str] = []
    required_confirmation: list[str] = []

    divergence = candidate.get("divergence", {})
    bollinger = candidate.get("bollinger", {})
    body_zone = candidate.get("body_zone", {})
    trendline = candidate.get("trendline", {})
    liquidity = candidate.get("liquidity", {})
    btc_context = candidate.get("btc_context", {})
    risk = candidate.get("risk", {})

    if risk.get("falling_knife_speed_pct", 0.0) <= -3.0:
        reject_reasons.append("falling_knife_risk")
    if divergence.get("divergence_strength", 0.0) < 60:
        reject_reasons.append("weak_divergence")
    if body_zone.get("body_zone_score", 0.0) < 30 and trendline.get("trendline_score", 0.0) < 30:
        reject_reasons.append("no_support")
    if btc_context.get("btc_drop_pct", 0.0) <= -1.5:
        reject_reasons.append("btc_shock")
    if liquidity.get("liquidity_score", 0.0) < 25:
        reject_reasons.append("low_liquidity")
    if body_zone.get("target_space_pct", 0.0) < 0.6:
        reject_reasons.append("bad_reward_risk")
    if not bollinger.get("reentered_lower_band", False):
        reject_reasons.append("no_bollinger_reentry")
    if risk.get("close_position", 1.0) < 0.45:
        reject_reasons.append("reentry_failure_risk")
    if risk.get("historical_profit_factor", 1.2) < 0.9:
        warnings.append("historical_weakness")

    score = 100.0 - len(reject_reasons) * 22 - len(warnings) * 8
    score = max(0.0, min(100.0, score))
    if reject_reasons:
        decision = "REJECT"
    elif warnings or score < 75:
        decision = "WARN"
        required_confirmation.append("confirmed_reentry_required")
    else:
        decision = "PASS"
    would_block = decision == "REJECT"
    blocking_applied = bool(would_block and blocking_enabled and mode == "BLOCKING")
    return {
        "skeptic_decision": decision,
        "skeptic_score": score,
        "reject_reasons": reject_reasons,
        "warnings": warnings,
        "required_confirmation": required_confirmation,
        "would_block": would_block,
        "blocking_applied": blocking_applied,
        "mode": mode,
    }
