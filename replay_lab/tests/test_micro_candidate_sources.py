from features.micro_candidate_sources import detect_micro_acceleration_candidate


def test_micro_acceleration_candidate_generation():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "price_change_3s_pct": 0.06, "price_change_5s_pct": 0.09, "buy_trade_ratio_5s": 0.6, "spread_pct": 0.1, "micro_strength_score": 70}
    assert detect_micro_acceleration_candidate(snap)["candidate_source"] == "MICRO_ACCELERATION"


def test_micro_acceleration_candidate_none_when_weak():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "price_change_3s_pct": 0.01, "price_change_5s_pct": 0.02, "buy_trade_ratio_5s": 0.6, "spread_pct": 0.1, "micro_strength_score": 70}
    assert detect_micro_acceleration_candidate(snap) is None
