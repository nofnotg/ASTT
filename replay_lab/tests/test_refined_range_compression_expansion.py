from features.refined_range_compression_expansion import detect_range_compression_expansion_refined


def test_refined_range_compression_expansion_candidate():
    snapshot = {"market": "KRW-X", "previous_high_distance_pct": 0.05, "volume_burst_ratio_10s_vs_60s": 1.3, "buy_trade_ratio_10s": 0.5, "orderbook_imbalance": 0.0, "spread_pct": 0.1, "bid_ask_size_ratio": 2.0}
    assert detect_range_compression_expansion_refined(snapshot)
    assert detect_range_compression_expansion_refined({**snapshot, "volume_burst_ratio_10s_vs_60s": 0.2}) is None
