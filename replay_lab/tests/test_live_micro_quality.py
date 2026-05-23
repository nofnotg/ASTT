from features.live_micro_quality import evaluate_live_micro_quality


def test_live_micro_quality_good_partial_unavailable():
    trades = [{"market": "KRW-BTC", "timestamp_ms": 1000}]
    orderbooks = [{"market": "KRW-BTC", "timestamp_ms": 1000}]

    assert evaluate_live_micro_quality(trades, orderbooks)["quality_grade"] == "GOOD"
    assert evaluate_live_micro_quality(trades, [])["quality_grade"] == "PARTIAL"
    assert evaluate_live_micro_quality([], [])["quality_grade"] == "UNAVAILABLE"
