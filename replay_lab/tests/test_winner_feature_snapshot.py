from winner_mining.winner_feature_snapshot import compute_winner_feature_snapshot


def test_winner_feature_snapshot_calculates_price_volume_buy_ratio():
    trades = [
        {"timestamp_ms": 1000, "trade_price": 100, "trade_volume": 1, "ask_bid": "BID"},
        {"timestamp_ms": 2000, "trade_price": 101, "trade_volume": 1, "ask_bid": "ASK"},
    ]
    snapshot = compute_winner_feature_snapshot(trades, [], 2000, 60)
    assert snapshot["price_change_pct"] == 1.0
    assert snapshot["volume"] == 2
    assert snapshot["buy_trade_ratio"] == 0.5
