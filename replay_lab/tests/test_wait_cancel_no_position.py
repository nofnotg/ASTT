from replay_lab.research.candidate_second_window_validation import _metrics
from replay_lab.replay.candidate_window_second_replay import replay_candidate_second_window


def test_wait_cancel_no_position_and_enter_only_pnl():
    rows = [
        {"entry_decision": "WAIT", "position_created": False, "included_in_pnl": False, "net_pnl_pct": None},
        {"entry_decision": "CANCEL", "position_created": False, "included_in_pnl": False, "net_pnl_pct": None},
        {"entry_decision": "ENTER", "position_created": True, "included_in_pnl": True, "net_pnl_pct": 0.2, "gross_pnl_pct": 0.35, "net_pnl_krw": 20.0, "hold_seconds": 5},
    ]

    metrics = _metrics(rows)

    assert rows[0]["position_created"] is False
    assert rows[1]["position_created"] is False
    assert metrics["entry_count"] == 1
    assert metrics["wait_count"] == 1
    assert metrics["cancel_count"] == 1
    assert metrics["total_pnl_krw_realistic_1"] == 20.0


def test_cancel_window_creates_observation_only_result():
    result = replay_candidate_second_window(
        {"candidate_time": "2026-05-23T09:00:00", "market": "KRW-BTC"},
        {"candidate_id": "c1", "market": "KRW-BTC", "candidate_time": "2026-05-23T09:00:00", "data_quality": "UNAVAILABLE", "seconds": []},
    )

    assert result["entry_decision"] == "CANCEL"
    assert result["position_created"] is False
    assert result["included_in_pnl"] is False
    assert result["net_pnl_pct"] is None
