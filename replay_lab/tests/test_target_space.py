from features.target_space import compute_target_space


def test_target_space_grade_and_rr():
    result = compute_target_space(100, 99, [{"zone_low": 102, "zone_high": 106}], [], {})
    assert result["risk_reward_1"] >= 1
    assert result["target_space_grade"] in {"B", "A", "A_PLUS"}
