from features.mtf_score import compute_v5_score


def test_v5_score_entry_allowed():
    result = compute_v5_score({"weekly_bias_score": 80, "daily_structure_score": 80, "h4_flow_score": 80, "structure_quality_score": 80, "setup_score": 80, "trigger_score": 80, "risk_reward": 1.5})
    assert result["entry_allowed"]
    assert result["v5_score"] >= 75
    assert compute_v5_score({"risk_reward": 0.5})["grade"] == "REJECT"
