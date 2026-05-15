from execution.skeptic_guard import evaluate_skeptic_guard


def _candidate(**overrides):
    base = {
        "divergence": {"divergence_strength": 80},
        "bollinger": {"reentered_lower_band": True},
        "body_zone": {"body_zone_score": 50, "target_space_pct": 1.0},
        "trendline": {"trendline_score": 50},
        "liquidity": {"liquidity_score": 60},
        "btc_context": {"btc_drop_pct": 0.0},
        "risk": {"falling_knife_speed_pct": -0.5, "close_position": 0.8},
    }
    base.update(overrides)
    return base


def test_skeptic_guard_rejects_key_risks_and_passes_normal_case():
    assert evaluate_skeptic_guard(_candidate(risk={"falling_knife_speed_pct": -4, "close_position": 0.8}))["skeptic_decision"] == "REJECT"
    assert evaluate_skeptic_guard(_candidate(body_zone={"body_zone_score": 0, "target_space_pct": 1.0}, trendline={"trendline_score": 0}))["skeptic_decision"] == "REJECT"
    assert evaluate_skeptic_guard(_candidate(liquidity={"liquidity_score": 10}))["skeptic_decision"] == "REJECT"
    assert evaluate_skeptic_guard(_candidate(body_zone={"body_zone_score": 50, "target_space_pct": 0.2}))["skeptic_decision"] == "REJECT"
    assert evaluate_skeptic_guard(_candidate())["skeptic_decision"] == "PASS"
