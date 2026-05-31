from __future__ import annotations


def select_agent(market_state: str) -> str:
    if market_state == "BULL_ATTACK":
        return "POLICY_BLEND_CONTROL"
    if market_state == "ALT_FRIENDLY":
        return "POLICY_BLEND_CONTROL"
    if market_state == "NORMAL":
        return "POLICY_BLEND_CONTROL"
    if market_state == "BTC_LED_MARKET":
        return "POLICY_BLEND_DOMINANCE_OVERLAY"
    if market_state == "EDGE_DECAY":
        return "RELATIVE_STRENGTH_BEAR_AGENT"
    if market_state == "RISK_OFF_ALT_WEAK":
        return "BEAR_DEFENSE_AGENT"
    if market_state == "BEAR_DEFENSE":
        return "CASH_DEFENSE_AGENT"
    if market_state == "BEAR_BOUNCE_ONLY":
        return "BEAR_BOUNCE_V2_RESEARCH_AGENT"
    if market_state == "LOCKDOWN":
        return "OBSERVATION_ONLY"
    return "POLICY_BLEND_CONTROL"
