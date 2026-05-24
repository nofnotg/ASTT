from timing_lab.calibration.armed_threshold_tuner import tune_armed_thresholds


def test_armed_state_calibrator_returns_target_rate_configs():
    result = tune_armed_thresholds("replay_store/timing_clips")
    assert result["armed_calibration"]
    assert any(row["recommendation"] == "KEEP" for row in result["armed_calibration"])
