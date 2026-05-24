from timing_lab.ring_buffer import MarketRingBuffer


def test_ring_buffer_keeps_window_and_extracts_pre_event_clip():
    buffer = MarketRingBuffer(window_seconds=600)
    buffer.append("KRW-TEST", {"type": "trade", "timestamp_ms": 0})
    buffer.append("KRW-TEST", {"type": "trade", "timestamp_ms": 700_000})
    assert len(buffer.get_events("KRW-TEST")) == 1
    assert buffer.extract_clip("KRW-TEST", 700_000, pre_seconds=600, post_seconds=10)
