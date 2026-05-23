from features.micro_feature_snapshot import build_micro_feature_snapshot


def test_micro_feature_snapshot_calculates_price_ratio_spread_and_state():
    trades = [
        {"market": "KRW-BTC", "timestamp_ms": 1000, "trade_price": 100, "trade_volume": 1, "ask_bid": "ASK"},
        {"market": "KRW-BTC", "timestamp_ms": 5000, "trade_price": 101, "trade_volume": 2, "ask_bid": "BID"},
    ]
    obs = [{"market": "KRW-BTC", "timestamp_ms": 5000, "units": [{"ask_price": 101.1, "bid_price": 101.0, "ask_size": 1, "bid_size": 2}]}]
    snap = build_micro_feature_snapshot("KRW-BTC", 5000, trades, obs)
    assert snap["price_change_3s_pct"] > 0
    assert snap["buy_trade_ratio_5s"] > 0
    assert snap["spread_pct"] > 0
    assert snap["orderbook_imbalance"] > 0
    assert snap["micro_state"] in {"ACCELERATING", "STABLE", "FADING", "REVERSING"}
