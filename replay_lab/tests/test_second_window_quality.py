from data.second_window_quality import evaluate_second_window_quality


def test_second_window_quality_grades():
    seconds = [{"time": f"2026-05-23T09:00:{i:02d}", "synthetic": False} for i in range(40)]
    result = evaluate_second_window_quality({"candidate_time": "2026-05-23T09:00:10", "seconds": seconds})
    assert result["quality_grade"] == "GOOD"

    result = evaluate_second_window_quality({"candidate_time": "2026-05-23T09:00:10", "seconds": []})
    assert result["quality_grade"] == "UNAVAILABLE"
