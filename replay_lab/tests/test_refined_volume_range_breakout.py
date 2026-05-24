from features.refined_volume_range_breakout import detect_volume_range_breakout_refined


def test_refined_volume_range_breakout_candidate():
    snapshot = {"market": "KRW-X", "volume_burst_ratio_10s_vs_60s": 1.5, "trade_count_acceleration": 1, "previous_high_distance_pct": 0.1, "breakout_distance_pct": 0.1, "spread_pct": 0.1, "bid_ask_size_ratio": 2.0}
    assert detect_volume_range_breakout_refined(snapshot)
    assert detect_volume_range_breakout_refined({**snapshot, "breakout_distance_pct": -0.1}) is None
