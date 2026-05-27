from __future__ import annotations

from btcd.btcdom_index_regime_classifier import classify_btcdom_index_regime, classify_btcdom_market_state


def test_btcdom_index_regime_classifier_rising_and_falling():
    assert classify_btcdom_index_regime({"btcdom_delta_7d": 2.0, "btcdom_zscore_90d": 0.5}) == "BTCDOM_RISING"
    assert classify_btcdom_index_regime({"btcdom_delta_7d": -2.0, "btcdom_zscore_90d": 0.0}) == "BTCDOM_FALLING"


def test_btcdom_market_state_combines_btc_trend():
    state = classify_btcdom_market_state({"btcdom_regime": "BTCDOM_RISING"}, {"btc_price_trend_4h": "DOWN"})
    assert state["market_state"] == "RISK_OFF_ALT_WEAK"
    state = classify_btcdom_market_state({"btcdom_regime": "BTCDOM_FALLING"}, {"btc_price_trend_4h": "SIDEWAYS"})
    assert state["market_state"] == "ALT_FRIENDLY"
