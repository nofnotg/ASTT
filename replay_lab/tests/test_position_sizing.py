from features.position_sizing import decide_position_size


def test_position_sizing_grades_and_risk_off():
    ok = decide_position_size(500000, "A_PLUS", "A_PLUS", {"fractal_state": "FULL_ALIGNMENT"}, {"alt_long_allowed": True, "position_size_multiplier": 1.0}, {"risk_decision": "PASS", "max_allowed_allocation_pct": 1.0})
    assert ok["allocation_pct"] >= 0.8
    off = decide_position_size(500000, "A_PLUS", "A_PLUS", {}, {"alt_long_allowed": False}, {"risk_decision": "PASS"})
    assert off["allocation_pct"] == 0
