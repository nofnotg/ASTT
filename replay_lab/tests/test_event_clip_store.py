from timing_lab.event_clip_store import EventClipStore
from timing_lab.ring_buffer import MarketRingBuffer
from replay_lab.tests.timing_lab_test_helpers import orderbook, trade


def test_event_clip_store_creates_closed_clip(tmp_path):
    buffer = MarketRingBuffer()
    for row in [trade(0, 100), orderbook(0), trade(2_000, 101), orderbook(2_000)]:
        buffer.append("KRW-TEST", row)
    event = {"event_id": "e1", "market": "KRW-TEST", "event_type": "VOLUME_SPIKE", "event_time_ms": 1_000}
    meta = EventClipStore(tmp_path).create_clip("s1", event, buffer, 10, 10)
    assert meta["status"] == "CLOSED"
    assert (tmp_path / "s1" / "e1_clip" / "clip_meta.json").exists()
