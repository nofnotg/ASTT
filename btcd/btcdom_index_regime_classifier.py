from __future__ import annotations

from typing import Any


def classify_btcdom_index_regime(feature: dict[str, Any]) -> str:
    delta_7d = float(feature.get("btcdom_delta_7d") or 0.0)
    zscore = float(feature.get("btcdom_zscore_90d") or 0.0)
    if zscore >= 2.0 and delta_7d > 0:
        return "BTCDOM_SPIKE"
    if zscore <= -2.0 and delta_7d < 0:
        return "BTCDOM_BREAKDOWN"
    if delta_7d > 0.75:
        return "BTCDOM_RISING"
    if delta_7d < -0.75:
        return "BTCDOM_FALLING"
    return "BTCDOM_STABLE"


def classify_btcdom_market_state(feature: dict[str, Any], btc_trend: dict[str, Any]) -> dict[str, Any]:
    regime = str(feature.get("btcdom_regime") or "BTCDOM_STABLE")
    trend = str(btc_trend.get("btc_price_trend_4h") or btc_trend.get("btc_price_trend_1d") or "SIDEWAYS")
    if trend in {"UP", "SIDEWAYS"} and regime in {"BTCDOM_FALLING", "BTCDOM_BREAKDOWN"}:
        state = "ALT_FRIENDLY"
    elif trend == "UP" and regime in {"BTCDOM_RISING", "BTCDOM_SPIKE"}:
        state = "BTC_LED_MARKET"
    elif trend == "DOWN" and regime in {"BTCDOM_RISING", "BTCDOM_SPIKE"}:
        state = "RISK_OFF_ALT_WEAK"
    elif trend == "DOWN" and regime in {"BTCDOM_FALLING", "BTCDOM_BREAKDOWN"}:
        state = "MARKET_WEAK_CASH_FLOW"
    else:
        state = "NORMAL"
    return {"market_state": state, "btcdom_regime": regime, "btc_trend": trend}
