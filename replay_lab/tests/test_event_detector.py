from timing_lab.event_detector import EventDetector
from timing_lab.ring_buffer import MarketRingBuffer
from replay_lab.tests.timing_lab_test_helpers import orderbook, trade


def test_event_detector_detects_core_events():
    buffer = MarketRingBuffer()
    for row in [trade(1, 100, 1, "ASK"), trade(2, 100, 1, "BID"), trade(3, 101, 10, "BID"), orderbook(1, 101, 99, 1), orderbook(3, 100.1, 100, 10000)]:
        buffer.append("KRW-TEST", row)
    types = {event["event_type"] for event in EventDetector().detect(buffer, "KRW-TEST")}
    assert {"VOLUME_SPIKE", "ORDERFLOW_SHIFT", "SPREAD_CONTRACTION", "DEPTH_RECOVERY"} & types
