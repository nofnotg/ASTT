from winner_mining.missed_winner_analyzer import _patterns


def test_missed_winner_patterns_support_count():
    traces = [{"trace_windows": {"T_MINUS_10S": {"volume_burst_ratio_10s_vs_60s": 2.0, "range_position_pct": 80, "buy_trade_ratio_10s": 0.6, "previous_high_distance_pct": 0.1}}}]
    patterns = _patterns(traces)
    assert any(row["support_count"] > 0 for row in patterns)
