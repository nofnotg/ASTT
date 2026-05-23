from features.orderbook_imbalance_candidate import detect_orderbook_imbalance_candidate


def test_orderbook_imbalance_candidate():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "bid_ask_size_ratio": 1.5, "orderbook_imbalance": 0.2, "buy_trade_ratio_3s": 0.6, "spread_pct": 0.1}
    assert detect_orderbook_imbalance_candidate(snap)["candidate_source"] == "ORDERBOOK_IMBALANCE"


def test_orderbook_imbalance_none_when_spread_wide():
    snap = {"market": "KRW-BTC", "timestamp_ms": 1, "last_price": 100, "bid_ask_size_ratio": 1.5, "orderbook_imbalance": 0.2, "buy_trade_ratio_3s": 0.6, "spread_pct": 0.5}
    assert detect_orderbook_imbalance_candidate(snap) is None
