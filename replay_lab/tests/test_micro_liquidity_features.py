from features.micro_liquidity_features import compute_micro_liquidity_features


def test_micro_liquidity_features_spread_and_state():
    result = compute_micro_liquidity_features([
        {"best_ask_price": 100.1, "best_bid_price": 100.0, "best_ask_size": 10, "best_bid_size": 20}
    ])

    assert result["spread_pct"] < 0.25
    assert result["bid_ask_size_ratio"] == 2
    assert result["liquidity_state"] == "BID_SUPPORT"


def test_micro_liquidity_wide_spread():
    result = compute_micro_liquidity_features([
        {"best_ask_price": 101.0, "best_bid_price": 100.0, "best_ask_size": 10, "best_bid_size": 10}
    ])

    assert result["liquidity_state"] == "WIDE_SPREAD"
