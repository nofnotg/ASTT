from tradable_winner.momentum_winner_detector import detect_momentum_winner


def test_momentum_winner_detector_rejects_liquidity_shortage():
    trades = [{"timestamp_ms": 0, "trade_price": 100}, {"timestamp_ms": 301000, "trade_price": 102}]
    orderbooks = [{"timestamp_ms": 0, "units": [{"ask_price": 100.1, "bid_price": 100.0, "ask_size": 100, "bid_size": 100} for _ in range(5)]}]
    result = detect_momentum_winner("KRW-AAA", "s1", trades[0], trades, orderbooks)
    assert "DEPTH_INSUFFICIENT" in result["prefilter"]["reject_reasons"]
