from __future__ import annotations

from typing import Any


def route_for_state(row: dict[str, Any]) -> dict[str, Any]:
    state = str(row.get("market_state") or "NORMAL")
    if state in {"BULL_ATTACK", "ALT_FRIENDLY", "NORMAL"}:
        return {"market_state": state, "route": "LG_V2_BALANCED_PLUS_DOM_GATE", "cap": 1.0}
    if state == "BTC_LED_MARKET":
        return {"market_state": state, "route": "LG_V2_BALANCED_PLUS_DOM_GATE", "cap": 0.70}
    if state == "EDGE_DECAY":
        return {"market_state": state, "route": "LG_M3_PF0.8_DD8", "cap": 0.35}
    if state == "RISK_OFF_ALT_WEAK":
        return {"market_state": state, "route": "BEAR_DEFENSE_SHADOW", "cap": 0.35}
    if state == "BEAR_DEFENSE":
        return {"market_state": state, "route": "CASH_DEFENSE_OR_A_PLUS_ONLY", "cap": 0.20}
    if state == "BEAR_BOUNCE_ONLY":
        return {"market_state": state, "route": "BEAR_BOUNCE_V3_SHADOW_ONLY", "cap": 0.25}
    if state == "LOCKDOWN":
        return {"market_state": state, "route": "OBSERVE_ONLY", "cap": 0.0}
    return {"market_state": state, "route": "LG_V2_BALANCED_PLUS_DOM_GATE", "cap": 1.0}
