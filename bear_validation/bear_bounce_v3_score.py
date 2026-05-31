from __future__ import annotations

from typing import Any


def score_bear_bounce_v3(context: dict[str, Any], prior_row: dict[str, Any] | None = None) -> dict[str, Any]:
    trade = context.get("trade", {})
    state = context.get("state", {})
    prior = prior_row or {}
    score = 0
    factors: list[str] = []
    market_state = str(state.get("market_state") or prior.get("market_state") or "")
    dominance = str(state.get("dominance_regime") or prior.get("dominance_regime") or "")
    btc_trend = str(state.get("btc_trend") or prior.get("btc_trend") or "")
    setup = str(trade.get("setup_type") or "")
    plan = str(trade.get("plan") or "")

    if market_state in {"RISK_OFF_ALT_WEAK", "BEAR_DEFENSE", "LOCKDOWN", "EDGE_DECAY"}:
        score += 18
        factors.append("BEAR_CONTEXT")
    if btc_trend != "DOWN":
        score += 10
        factors.append("BTC_DROP_EASING_PROXY")
    if "SPIKE" not in dominance:
        score += 8
        factors.append("DOMINANCE_EASING_PROXY")
    if "SWEEP" in setup or "REVERSAL" in setup:
        score += 16
        factors.append("SWEEP_OR_REVERSAL")
    if plan == "PLAN_A_ICT_FAT_TAIL":
        score += 12
        factors.append("PLAN_A_STRUCTURE")
    if float(trade.get("return_pct", 0.0)) > 0.0:
        score += 10
        factors.append("RECLAIM_OUTCOME_PROXY")
    if float(prior.get("drawdown_before_pct", prior.get("drawdown_pct", 0.0))) <= -8.0:
        score += 10
        factors.append("DEEP_HWM_CONTEXT")
    if bool(prior.get("hard_guard")):
        score += 6
        factors.append("HARD_GUARD_CONTEXT")
    score = min(score, 100)
    return {
        "bear_bounce_v3_score": score,
        "bear_bounce_v3_candidate": score >= 60,
        "bear_bounce_v3_high_confidence": score >= 75,
        "bear_bounce_v3_factors": factors,
    }
