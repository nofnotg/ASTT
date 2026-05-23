from features.micro_momentum_breakdown import breakdown_micro_momentum


def test_micro_momentum_breakdown_returns_weak_reasons():
    result = breakdown_micro_momentum({"micro_state": "FADING", "price_change_3s_pct": 0.0, "buy_trade_ratio_5s": 0.4, "volume_5s": 0.0, "orderbook_imbalance": 0.0, "spread_pct": 0.1})
    assert "PRICE_ACCELERATION_LOW" in result["weak_reasons"]
    assert "BUY_TRADE_RATIO_LOW" in result["weak_reasons"]
    assert "VOLUME_BURST_ABSENT" in result["weak_reasons"]
