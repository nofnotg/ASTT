from execution.skeptic_guard import evaluate_skeptic_guard


def _bad_candidate() -> dict:
    return {
        "divergence": {"divergence_strength": 40},
        "bollinger": {"reentered_lower_band": False},
        "body_zone": {"body_zone_score": 0, "target_space_pct": 0.2},
        "trendline": {"trendline_score": 0},
        "liquidity": {"liquidity_score": 80},
        "btc_context": {"btc_drop_pct": 0},
        "risk": {"falling_knife_speed_pct": -4, "close_position": 0.3},
    }


def test_diagnostic_records_reject_without_applying_block():
    result = evaluate_skeptic_guard(_bad_candidate(), mode="DIAGNOSTIC", blocking_enabled=False)
    assert result["skeptic_decision"] == "REJECT"
    assert result["would_block"] is True
    assert result["blocking_applied"] is False


def test_blocking_mode_applies_reject_block():
    result = evaluate_skeptic_guard(_bad_candidate(), mode="BLOCKING", blocking_enabled=True)
    assert result["would_block"] is True
    assert result["blocking_applied"] is True
