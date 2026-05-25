from __future__ import annotations

from typing import Any


def route_policy(trade: dict[str, Any], states: list[str], quality_score: float, defense_state: str) -> dict[str, Any]:
    plan = str(trade.get("plan", ""))
    setup = str(trade.get("setup_type", ""))
    if "MA_BEAR" in states or "TESTA_LOST_75" in states:
        return {"policy": "PLAN_C_NO_TRADE", "multiplier_scale": 0.0, "reason": ["MA_BEAR_OR_LOST_75"]}
    if defense_state == "DEFENSIVE" and ("MA_CHOP" in states or "TESTA_CHOP" in states):
        return {"policy": "PLAN_C_NO_TRADE", "multiplier_scale": 0.0, "reason": ["DEFENSIVE_MA_CHOP"]}
    if defense_state == "DEFENSIVE" and quality_score >= 85:
        return {"policy": "ROLLING_EDGE_THROTTLE", "multiplier_scale": 0.35, "reason": ["DEFENSIVE_A_PLUS_ONLY"]}
    if "MA_CHOP" in states or "TESTA_CHOP" in states:
        return {"policy": "PLAN_C_NO_TRADE", "multiplier_scale": 0.35, "reason": ["MA_CHOP_REDUCE"]}
    if "MA_OVEREXTENDED" in states:
        return {"policy": "PLAN_D_OBSERVATION", "multiplier_scale": 0.0, "reason": ["MA_OVEREXTENDED_OBSERVE"]}
    if plan == "PLAN_A_ICT_FAT_TAIL" and "FVG_OB_OVERLAP" in setup and "MA_BULL" in states:
        return {"policy": "ROLLING_EDGE_THROTTLE", "multiplier_scale": 1.0, "reason": ["PLAN_A_ROLLING_IN_MA_BULL"]}
    if plan == "PLAN_B_COMBINED_CONTEXT" and ("MA_BULL" in states or "TESTA_BULL_ALIGNMENT" in states):
        return {"policy": "BALANCED_GROWTH", "multiplier_scale": 1.0, "reason": ["PLAN_B_BALANCED_IN_MA_BULL"]}
    return {"policy": "BALANCED_GROWTH", "multiplier_scale": 0.7 if quality_score < 60 else 1.0, "reason": ["DEFAULT_MA_ROUTER"]}
