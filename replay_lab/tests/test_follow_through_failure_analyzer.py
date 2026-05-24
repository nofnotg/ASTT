from timing_lab.follow_through_failure_analyzer import _analyze_state


def test_follow_through_failure_analyzer_classifies_price_no_move_and_move_too_small():
    state = {"event_id": "e", "market": "KRW-BTC", "state_entered_at_ms": 1000, "evidence": {"buy_trade_ratio": 0.6}}
    meta = {"event_time_ms": 1000}
    no_move = _analyze_state(state, meta, [{"timestamp_ms": 1000, "trade_price": 100, "ask_bid": "BID"}, {"timestamp_ms": 2000, "trade_price": 100, "ask_bid": "ASK"}], [])
    small = _analyze_state(state, meta, [{"timestamp_ms": 1000, "trade_price": 100, "ask_bid": "BID"}, {"timestamp_ms": 2000, "trade_price": 100.04, "ask_bid": "BID"}], [])
    assert no_move["failure_type"] == "PRICE_NO_MOVE"
    assert small["failure_type"] == "MOVE_TOO_SMALL"
