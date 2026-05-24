from timing_lab.calibration.confirmation_threshold_tuner import tune_confirmation_thresholds


def test_confirmation_calibrator_reports_confirmed_zero_reason():
    result = tune_confirmation_thresholds("replay_store/timing_clips")
    assert result["confirmation_calibration"]
    assert "confirmed_zero_reason" in result
