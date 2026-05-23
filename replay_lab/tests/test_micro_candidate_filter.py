from features.micro_candidate_filter import apply_micro_candidate_filter


def _window(synthetic=False, close_step=0.02):
    seconds = []
    for i in range(40):
        seconds.append({"time": f"2026-05-23T09:00:{i:02d}", "open": 100 + i * close_step, "high": 100 + i * close_step, "low": 100 + i * close_step, "close": 100 + i * close_step, "volume": 1, "synthetic": synthetic})
    return {"candidate_id": "c1", "market": "KRW-BTC", "candidate_time": "2026-05-23T09:00:20", "seconds": seconds, "quality": {"actual_coverage_pct": 100, "critical_window_coverage_pct": 100}}


def test_micro_candidate_filter_rejects_cost_too_large():
    candidate = {"candidate_id": "c1", "candidate_time": "2026-05-23T09:00:20", "reference_price": 100, "target_price": 100.2}

    result = apply_micro_candidate_filter(candidate, _window())

    assert result["micro_candidate_decision"] == "REJECT"
    assert "target_too_small_vs_cost" in result["reject_reasons"]


def test_micro_candidate_filter_rejects_low_critical_coverage():
    candidate = {"candidate_id": "c1", "candidate_time": "2026-05-23T09:00:20", "reference_price": 100, "target_price": 101}
    window = _window(synthetic=True)
    window["quality"] = {"actual_coverage_pct": 0, "critical_window_coverage_pct": 0}

    result = apply_micro_candidate_filter(candidate, window)

    assert result["micro_candidate_decision"] == "REJECT"
    assert "critical_window_no_actual_seconds" in result["reject_reasons"]


def test_micro_candidate_filter_passes_when_cost_and_coverage_are_ok():
    candidate = {"candidate_id": "c1", "candidate_time": "2026-05-23T09:00:20", "reference_price": 100, "target_price": 101}

    result = apply_micro_candidate_filter(candidate, _window())

    assert result["micro_candidate_decision"] == "PASS"
    assert result["cost_to_target_ratio"] < 0.3
