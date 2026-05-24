from capital.exposure_guard import check_exposure_guard


def test_exposure_guard_blocks_high_risk():
    result = check_exposure_guard({"equity_krw": 500000, "head_controller_risk_level": "HIGH"}, {"max_open_positions": 1, "max_total_exposure_pct": 1.0}, 10000)
    assert result["allowed"] is False
    assert result["reason"] == "HEAD_CONTROLLER_HIGH_RISK"
