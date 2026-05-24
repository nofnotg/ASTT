from tradable_winner.spike_winner_detector import detect_spike_winner


def test_spike_winner_detector_requires_reward_to_cost():
    trades = [{"timestamp_ms": 0, "trade_price": 100}, {"timestamp_ms": 901000, "trade_price": 100.5}]
    orderbooks = [{"timestamp_ms": 0, "units": [{"ask_price": 100.1, "bid_price": 100.0, "ask_size": 20000, "bid_size": 20000} for _ in range(5)]}]
    result = detect_spike_winner("KRW-AAA", "s1", trades[0], trades, orderbooks)
    assert "EFFECTIVE_RETURN_TOO_LOW" in result["prefilter"]["reject_reasons"]
