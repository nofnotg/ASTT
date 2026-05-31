from __future__ import annotations

from typing import Any


def classify_market_state(feature: dict[str, Any], btc_feature: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify market state from only decision-time-safe features."""
    btc_feature = btc_feature or {}
    regime = str(feature.get("dominance_regime") or feature.get("btcdom_regime") or "DOM_STABLE")
    delta_7d = _num(feature.get("dominance_delta_7d", feature.get("btcdom_delta_7d", 0.0)))
    delta_30d = _num(feature.get("dominance_delta_30d", feature.get("btcdom_delta_30d", 0.0)))
    btc_return = _num(btc_feature.get("btc_return_7d_pct", btc_feature.get("return_7d_pct", 0.0)))

    if regime in {"DOM_BREAKDOWN"} or delta_7d <= -2.0:
        state = "ALT_FRIENDLY" if btc_return >= -3.0 else "EDGE_DECAY"
    elif regime in {"DOM_SPIKE"} or delta_7d >= 2.0:
        state = "BTC_LED_MARKET" if btc_return >= 0 else "RISK_OFF_ALT_WEAK"
    elif btc_return <= -8.0 and delta_30d >= 0:
        state = "BEAR_DEFENSE"
    elif btc_return <= -12.0:
        state = "LOCKDOWN"
    elif btc_return >= 6.0 and delta_7d <= 1.0:
        state = "BULL_ATTACK"
    else:
        state = "NORMAL"
    return {"market_state": state, "dominance_regime": regime}


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
