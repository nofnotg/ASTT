from winner_mining.winner_event_detector import build_second_series, detect_winner_events


def _seconds(prices, step=1000):
    return [{"market": "KRW-ABC", "timestamp_ms": i * step, "price": p, "high": p} for i, p in enumerate(prices)]


def test_micro_winner_detected():
    prices = [100.0] * 30 + [100.5]
    events = detect_winner_events(_seconds(prices), ["MICRO_WINNER"])
    assert events
    assert events[0]["winner_type"] == "MICRO_WINNER"


def test_scalp_momentum_spike_winners_detected():
    prices = [100.0] * 180 + [100.8] + [101.6] * 120 + [103.2]
    events = detect_winner_events(_seconds(prices), ["SCALP_WINNER", "MOMENTUM_WINNER", "SPIKE_WINNER"])
    assert {event["winner_type"] for event in events} & {"SCALP_WINNER", "MOMENTUM_WINNER", "SPIKE_WINNER"}


def test_second_series_groups_trades():
    trades = [
        {"market": "KRW-ABC", "timestamp_ms": 1000, "trade_price": 100, "trade_volume": 1, "ask_bid": "BID"},
        {"market": "KRW-ABC", "timestamp_ms": 1500, "trade_price": 101, "trade_volume": 2, "ask_bid": "ASK"},
    ]
    rows = build_second_series(trades)
    assert len(rows) == 1
    assert rows[0]["high"] == 101
    assert rows[0]["volume"] == 3
