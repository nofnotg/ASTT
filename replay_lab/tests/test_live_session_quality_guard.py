from live_capture.live_session_quality_guard import evaluate_live_session_quality


def test_live_session_quality_guard_grades_counts():
    assert evaluate_live_session_quality(100, 100, 10, 1)["quality"] == "GOOD"
    assert evaluate_live_session_quality(0, 0, 0, 1)["quality"] == "POOR"
