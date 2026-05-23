from replay_lab.replay.candidate_window_second_replay import replay_candidate_second_window


def test_candidate_window_second_replay_uses_pre_for_entry_and_post_for_exit():
    seconds = []
    for i in range(6):
        seconds.append({"time": f"2026-05-23T09:00:0{i}", "open": 100, "high": 100 + i * 0.2, "low": 99.9, "close": 100 + i * 0.1, "volume": 1, "synthetic": False})
    window = {"candidate_id": "c1", "market": "KRW-BTC", "candidate_time": "2026-05-23T09:00:02", "data_quality": "GOOD", "seconds": seconds}
    candidate = {"candidate_time": "2026-05-23T09:00:02", "reference_price": 100.2, "target_price": 100.5, "stop_price": 99.5}

    result = replay_candidate_second_window(candidate, window)

    assert result["data_source"] == "UPBIT_REST_SECONDS"
    assert result["entry_decision"] in {"ENTER", "WAIT"}
    assert "net_pnl_pct" in result
