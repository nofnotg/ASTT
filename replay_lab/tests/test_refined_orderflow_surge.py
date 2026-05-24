from features.refined_orderflow_surge import detect_orderflow_surge_refined


def test_refined_orderflow_surge_candidate():
    snapshot = {"market": "KRW-X", "buy_trade_ratio_5s": 0.6, "buy_trade_ratio_10s": 0.55, "orderbook_imbalance": 0.2, "spread_pct": 0.1, "bid_ask_size_ratio": 2.0}
    assert detect_orderflow_surge_refined(snapshot)
    assert detect_orderflow_surge_refined({**snapshot, "buy_trade_ratio_10s": 0.1}) is None
