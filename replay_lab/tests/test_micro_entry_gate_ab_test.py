from execution.micro_entry_gate_ab_test import run_micro_entry_gate_abtest


def test_micro_entry_gate_abtest_separates_profiles_and_keeps_wait_out_of_pnl():
    candidates = [
        {"data_quality": "GOOD", "primary_block_reason": "MICRO_STATE_WEAK", "block_reasons": ["MICRO_STATE_WEAK"], "gate_values": {"micro_state": "FADING", "cost_to_target_ratio": 0.2}},
        {"data_quality": "POOR", "primary_block_reason": "DATA_QUALITY_POOR", "block_reasons": ["DATA_QUALITY_POOR"], "gate_values": {"micro_state": "STABLE", "cost_to_target_ratio": 0.1}},
    ]

    result = run_micro_entry_gate_abtest(candidates)

    assert result["profiles"]["STRICT"]["wait_count"] >= 1
    assert result["profiles"]["EXPLORATORY"]["research_only"] is True
    assert result["profiles"]["STRICT"]["pf_realistic_1"] == 0.0
