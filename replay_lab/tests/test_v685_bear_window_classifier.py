from __future__ import annotations

from bear_window.bear_window_classifier import classify_window


def test_v685_bear_window_classifier_prioritizes_risk_off() -> None:
    assert classify_window({"market_state": "RISK_OFF_ALT_WEAK", "dominance_regime": "BTCDOM_RISING"}) == "RISK_OFF_WINDOW"


def test_v685_bear_window_classifier_detects_btc_led_alt_weak() -> None:
    assert classify_window({"market_state": "NORMAL", "dominance_regime": "BTCDOM_SPIKE"}) == "BTC_LED_ALT_WEAK_WINDOW"
