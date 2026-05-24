from timing_lab.calibration.calibration_grid_runner import run_calibration_grid


def test_calibration_grid_runner_returns_top_three():
    result = run_calibration_grid("replay_store/timing_clips")
    assert len(result["top_3"]) <= 3
    assert "estimated_quality_score" in result["top_3"][0]
