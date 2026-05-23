import json

from execution.realistic_paper_runner import run_realistic_paper_session_v555


def test_realistic_paper_runner_creates_summary_and_keeps_orders_disabled(monkeypatch, tmp_path):
    import execution.realistic_paper_runner as runner

    def fake_ws(markets, duration_seconds, include_trade=True, include_orderbook=True):
        raw = tmp_path / "raw" / "upbit_ws" / "2026-05-24" / "ws1"
        (raw / "trades").mkdir(parents=True)
        (raw / "orderbooks").mkdir(parents=True)
        trade = {"market": markets[0], "timestamp_ms": 10000, "trade_price": 100, "trade_volume": 1, "ask_bid": "BID"}
        ob = {"market": markets[0], "timestamp_ms": 10000, "units": [{"ask_price": 100.1, "bid_price": 100.0, "ask_size": 1, "bid_size": 2}]}
        (raw / "trades" / f"{markets[0]}.jsonl").write_text(json.dumps(trade) + "\n", encoding="utf-8")
        (raw / "orderbooks" / f"{markets[0]}.jsonl").write_text(json.dumps(ob) + "\n", encoding="utf-8")
        return {"session_id": "ws1", "markets": markets, "trade_event_count": 1, "orderbook_event_count": 1}

    monkeypatch.setattr(runner, "REPLAY_STORE_DIR", tmp_path)
    monkeypatch.setattr(runner, "run_upbit_real_ws_session", fake_ws)
    result = run_realistic_paper_session_v555(duration_minutes=1, top_markets=1)
    assert result["real_order_enabled"] is False
    assert (tmp_path / "sessions" / "realistic_paper_v555" / result["session_id"] / "session_summary.json").exists()
