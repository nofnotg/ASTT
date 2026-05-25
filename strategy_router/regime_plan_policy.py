from __future__ import annotations

from strategy_router.strategy_plan_schema import PLAN_A, PLAN_B, PLAN_C, PLAN_D


def route_for_regime(regime: str) -> dict:
    if regime == "ALT_ROTATION":
        return {"enabled_plans": [PLAN_A, PLAN_B], "disabled_plans": [PLAN_C], "risk_multiplier": 1.0}
    if regime == "HIGH_VOLATILITY":
        return {"enabled_plans": [PLAN_A, PLAN_B], "disabled_plans": [PLAN_C], "risk_multiplier": 0.8}
    if regime in {"CHOP", "RISK_OFF"}:
        return {"enabled_plans": [PLAN_C, PLAN_D], "disabled_plans": [PLAN_A, PLAN_B], "risk_multiplier": 0.0}
    return {"enabled_plans": [PLAN_D], "disabled_plans": [PLAN_A, PLAN_B], "risk_multiplier": 0.0}
