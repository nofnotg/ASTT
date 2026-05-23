from features.vwap_reclaim_candidate import detect_vwap_reclaim_candidate


def test_vwap_reclaim_candidate():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 101, "buy_trade_ratio_5s": 0.6, "spread_pct": 0.1, "micro_state": "STABLE"}
    assert detect_vwap_reclaim_candidate("KRW-BTC", snap, {"vwap": 100, "previous_price": 99})["candidate_source"] == "VWAP_RECLAIM"


def test_vwap_reclaim_none_without_reclaim():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 99, "buy_trade_ratio_5s": 0.6, "spread_pct": 0.1, "micro_state": "STABLE"}
    assert detect_vwap_reclaim_candidate("KRW-BTC", snap, {"vwap": 100, "previous_price": 99}) is None
