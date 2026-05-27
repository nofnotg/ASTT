from __future__ import annotations

from btcd.btcd_market_regime_classifier import classify_btcd_market_regime


def test_btcd_market_regime_classifier_alt_friendly():
    regime = classify_btcd_market_regime({"btcd_regime": "BTCD_FALLING"}, {"btc_price_trend_4h": "UP"})
    assert regime["market_regime"] == "ALT_FRIENDLY"
    assert regime["alt_permission"] == "ALLOW"
