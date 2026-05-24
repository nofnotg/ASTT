from winner_mining.winner_trace_extractor import _feature_set


def test_winner_trace_feature_uses_only_as_of_time():
    trades = [
        {"market": "KRW-ABC", "timestamp_ms": 1000, "trade_price": 100, "trade_volume": 1, "ask_bid": "BID"},
        {"market": "KRW-ABC", "timestamp_ms": 2000, "trade_price": 101, "trade_volume": 1, "ask_bid": "BID"},
        {"market": "KRW-ABC", "timestamp_ms": 3000, "trade_price": 150, "trade_volume": 1, "ask_bid": "BID"},
    ]
    features = _feature_set(trades, [], 2000)
    assert features["price_change_3s_pct"] < 50
