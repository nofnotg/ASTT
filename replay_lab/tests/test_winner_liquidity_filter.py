from winner_mining.winner_liquidity_filter import estimate_liquidity_from_trace


def test_liquidity_filter_requires_narrow_spread_and_depth():
    trace = {"trace_windows": {"T_MINUS_10S": {"spread_pct": 0.1, "bid_ask_size_ratio": 1.5}}}
    assert estimate_liquidity_from_trace(trace, 1000)["tradable_with_500k"] is True
    wide = {"trace_windows": {"T_MINUS_10S": {"spread_pct": 0.4, "bid_ask_size_ratio": 1.5}}}
    assert estimate_liquidity_from_trace(wide, 1000)["tradable_with_500k"] is False
