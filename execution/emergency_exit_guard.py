from __future__ import annotations


def check_emergency_exit(btc_micro_context: dict, market_micro_context: dict, orderbook_context=None) -> dict:
    reasons = []
    if btc_micro_context.get("price_change_5s_pct", 0.0) <= -0.35 or btc_micro_context.get("price_change_10s_pct", 0.0) <= -0.7:
        reasons.append("BTC_MICRO_SHOCK")
    if market_micro_context.get("micro_state") == "REVERSING":
        reasons.append("MARKET_REVERSING")
    if orderbook_context:
        if orderbook_context.get("spread_pct", 0.0) > 0.4:
            reasons.append("SPREAD_SHOCK")
        if orderbook_context.get("orderbook_imbalance", 0.0) < -0.7:
            reasons.append("ORDERBOOK_COLLAPSE")
    severity = "HIGH" if len(reasons) >= 2 else ("MEDIUM" if reasons else "LOW")
    return {"emergency": bool(reasons), "reason": reasons, "severity": severity}
