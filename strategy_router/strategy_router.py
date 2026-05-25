from __future__ import annotations

from analysis.regime_performance_analyzer import classify_trade_regime
from strategy_router.regime_plan_policy import route_for_regime
from strategy_router.strategy_plan_schema import PLAN_A, PLAN_B, PLAN_C, PLAN_D


def plan_for_trade(trade: dict) -> dict:
    regime = classify_trade_regime(trade)
    policy = route_for_regime(regime)
    strategy = trade.get("strategy", "")
    setup = trade.get("setup_type", "")
    if strategy == "ICT_FVG_OB_SWEEP" and PLAN_A in policy["enabled_plans"]:
        plan = PLAN_A
    elif strategy == "COMBINED_VOLUME_ICT" and PLAN_B in policy["enabled_plans"]:
        plan = PLAN_B
    elif policy["risk_multiplier"] == 0.0:
        plan = PLAN_C
    else:
        plan = PLAN_D
    return {
        "regime": regime,
        "plan": plan,
        "enabled_plans": policy["enabled_plans"],
        "disabled_plans": policy["disabled_plans"],
        "risk_multiplier": policy["risk_multiplier"],
        "reason": [f"strategy={strategy}", f"setup={setup}", f"regime={regime}"],
    }
