from tradable_winner.scalp_winner_detector import detect_scalp_winner


def test_scalp_winner_detector_accepts_effective_return():
    trades = [{"timestamp_ms": 0, "trade_price": 100}, {"timestamp_ms": 181000, "trade_price": 104}]
    orderbooks = [{"timestamp_ms": 0, "units": [{"ask_price": 100.1, "bid_price": 100.0, "ask_size": 20000, "bid_size": 20000} for _ in range(5)]}]
    result = detect_scalp_winner("KRW-AAA", "s1", trades[0], trades, orderbooks)
    assert result["prefilter"]["prefilter_pass"] is True
