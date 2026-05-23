import json

from live_data.live_micro_storage import LiveMicroStorage


def test_live_micro_storage_writes_jsonl_parquet_and_summary(tmp_path):
    storage = LiveMicroStorage("session_test", root=tmp_path)
    event = {"market": "KRW-BTC", "timestamp_ms": 1770000000000, "trade_price": 100, "trade_volume": 1, "ask_bid": "BID"}
    storage.append_trade(event)
    storage.append_orderbook({"market": "KRW-BTC", "timestamp_ms": 1770000000000, "units": []})
    storage.normalize_to_parquet()
    summary = storage.write_summary(status="COMPLETED")

    assert list((tmp_path / "raw" / "live_micro").glob("*/trades/KRW-BTC.jsonl"))
    assert list((tmp_path / "normalized" / "live_micro").glob("*/trades/KRW-BTC.parquet"))
    assert json.loads(summary.read_text(encoding="utf-8"))["trade_event_count"] == 1
