from timing_lab.market_recorder import MarketRecorder


def test_market_recorder_records_event_types_and_btc_quality():
    recorder = MarketRecorder()
    recorder.record({"type": "trade", "market": "KRW-BTC", "timestamp_ms": 1, "trade_price": 1})
    recorder.record({"type": "orderbook", "market": "KRW-BTC", "timestamp_ms": 2, "units": []})
    summary = recorder.summary()
    assert summary["btc_included"] is True
    assert summary["quality"] == "GOOD"
