from features.micro_execution_feasibility import assess_micro_execution_feasibility


def test_micro_execution_feasibility_rejects_cost_and_spread():
    result = assess_micro_execution_feasibility({"expected_target_pct": 0.6}, {"spread_pct": 0.1, "liquidity_state": "GOOD"}, {"cost_pct": 0.3})
    assert result["decision"] == "TOO_EXPENSIVE"

    result = assess_micro_execution_feasibility({"expected_target_pct": 0.6}, {"spread_pct": 999, "liquidity_state": "NO_DATA"}, {"cost_pct": 0.01})
    assert result["decision"] == "NO_DATA"
