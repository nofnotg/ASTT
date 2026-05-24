from timing_lab.timing_project_scorecard import build_project_scorecard


def test_project_scorecard_v5r2_has_total_and_decision():
    result = build_project_scorecard()
    assert "total_score" in result
    assert result["project_decision"] in {"CONTINUE", "PAUSE", "KILL_RECOMMENDED"}
