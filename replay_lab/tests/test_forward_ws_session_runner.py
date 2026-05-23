from execution.forward_ws_session_runner import run_forward_ws_session_v554


def test_forward_ws_session_runner_forces_real_order_disabled(monkeypatch, tmp_path):
    import execution.forward_ws_session_runner as runner

    def fake_session(markets, duration_seconds, include_trade=True, include_orderbook=True):
        return {
            "session_id": "s1",
            "markets": markets,
            "duration_seconds": duration_seconds,
            "trade_event_count": 1,
            "orderbook_event_count": 1,
            "trade_event_count_by_market": {markets[0]: 1},
            "orderbook_event_count_by_market": {markets[0]: 1},
            "status": "COMPLETED",
        }

    monkeypatch.setattr(runner, "REPLAY_STORE_DIR", tmp_path)
    monkeypatch.setattr(runner, "run_upbit_real_ws_session", fake_session)

    result = run_forward_ws_session_v554(duration_minutes=1, top_markets=1)

    assert result["real_order_enabled"] is False
    assert result["candidate_count"] == 3
    assert (tmp_path / "sessions" / "forward_ws_v554" / "s1" / "session_summary.json").exists()
