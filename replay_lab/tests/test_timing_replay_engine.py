import json
from replay_lab.tests.timing_lab_test_helpers import orderbook, trade
import timing_lab.timing_replay_engine as replay_engine


def test_timing_replay_engine_replays_recorded_without_lookahead(tmp_path, monkeypatch):
    monkeypatch.setattr(replay_engine, "REPLAY_STORE_DIR", tmp_path / "store")
    session = tmp_path / "s1" / "trades"
    session.mkdir(parents=True)
    (session / "KRW-TEST.jsonl").write_text("\n".join(json.dumps(trade(i * 1000, 100 + i, 10)) for i in range(4)), encoding="utf-8")
    ob = tmp_path / "s1" / "orderbooks"
    ob.mkdir()
    (ob / "KRW-TEST.jsonl").write_text("\n".join(json.dumps(orderbook(i * 1000)) for i in range(4)), encoding="utf-8")
    summary = replay_engine.replay_timing_lab_v5r1(tmp_path, 30, 30)
    assert summary["real_order_enabled"] is False
