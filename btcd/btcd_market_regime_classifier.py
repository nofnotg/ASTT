from __future__ import annotations

from typing import Any


def classify_btcd_market_regime(btcd_feature: dict[str, Any], btc_trend: dict[str, Any]) -> dict[str, Any]:
    btcd = btcd_feature.get("btcd_regime", "BTCD_UNAVAILABLE")
    btc = btc_trend.get("btc_price_trend_4h") or btc_trend.get("btc_price_trend_1d") or "SIDEWAYS"
    if btcd == "BTCD_UNAVAILABLE":
        regime = "GLOBAL_BTCD_UNAVAILABLE"
    elif btc == "UP" and btcd in {"BTCD_FALLING", "BTCD_BREAKDOWN"}:
        regime = "ALT_FRIENDLY"
    elif btc == "UP" and btcd in {"BTCD_RISING", "BTCD_SPIKE"}:
        regime = "BTC_LED_MARKET"
    elif btc == "DOWN" and btcd in {"BTCD_RISING", "BTCD_SPIKE"}:
        regime = "RISK_OFF_ALT_WEAK"
    elif btc == "DOWN" and btcd in {"BTCD_FALLING", "BTCD_BREAKDOWN"}:
        regime = "MARKET_WEAK_CASH_FLOW"
    elif btc == "SIDEWAYS" and btcd in {"BTCD_FALLING", "BTCD_BREAKDOWN"}:
        regime = "ALT_FRIENDLY"
    elif btc == "SIDEWAYS" and btcd in {"BTCD_RISING", "BTCD_SPIKE"}:
        regime = "BTC_LED_MARKET"
    else:
        regime = "NEUTRAL"
    return {
        "market_regime": regime,
        "btc_trend": btc,
        "btcd_regime": btcd,
        "alt_permission": _permission(regime),
        "reason": [btc, btcd],
    }


def _permission(regime: str) -> str:
    if regime == "ALT_FRIENDLY":
        return "ALLOW"
    if regime == "BTC_LED_MARKET":
        return "REDUCE"
    if regime == "RISK_OFF_ALT_WEAK":
        return "RESTRICT"
    if regime == "MARKET_WEAK_CASH_FLOW":
        return "OBSERVE"
    if regime == "GLOBAL_BTCD_UNAVAILABLE":
        return "DATA_REQUIRED"
    return "ALLOW"
