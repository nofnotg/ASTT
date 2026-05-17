from __future__ import annotations


def evaluate_full_seed_risk_gate(candidate: dict, max_allowed_stop_pct: float = 1.5, max_consecutive_losses: int = 2) -> dict:
    veto = []
    warnings = []
    regime = candidate.get("btc_regime", {})
    target = candidate.get("target_space", {})
    if regime.get("alt_regime") == "RISK_OFF" or not regime.get("alt_long_allowed", True):
        veto.append("ALT_RISK_OFF")
    if target.get("target_space_grade") == "REJECT":
        veto.append("target_space_reject")
    if float(target.get("risk_reward_1", 0.0)) < 1.0:
        veto.append("risk_reward_1_below_1")
    if float(target.get("risk_pct", 0.0)) > max_allowed_stop_pct:
        warnings.append("stop_pct_high")
    if float(candidate.get("zone_width_pct", 0.0)) > 4.0:
        veto.append("zone_width_too_wide")
    if candidate.get("data_quality") == "LOW":
        veto.append("data_quality_low")
    if float(candidate.get("current_equity_drawdown", 0.0)) < -8.0:
        veto.append("equity_drawdown_limit")
    if int(candidate.get("consecutive_loss", 0)) >= max_consecutive_losses:
        warnings.append("consecutive_loss_size_reduction")
    max_alloc = 1.0
    if "stop_pct_high" in warnings:
        max_alloc = min(max_alloc, 0.5)
    if "consecutive_loss_size_reduction" in warnings:
        max_alloc = min(max_alloc, 0.5)
    decision = "REJECT" if veto else "WARN" if warnings else "PASS"
    return {"risk_decision": decision, "max_allowed_allocation_pct": 0.0 if veto else max_alloc, "veto": bool(veto), "veto_reasons": veto, "warnings": warnings}
