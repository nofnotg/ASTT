from features.micro_entry_gate_diagnostics import diagnose_micro_entry_gates, summarize_gate_diagnostics


def test_micro_entry_gate_diagnostics_classifies_block_reasons():
    result = diagnose_micro_entry_gates(
        {"candidate_id": "c1", "market": "KRW-BTC", "entry_decision": "WAIT", "data_quality": "GOOD"},
        {"data_quality": "GOOD"},
        micro_signal={"buy_trade_ratio_5s": 0.48, "micro_state": "FADING"},
        micro_liquidity={"liquidity_state": "NO_DATA"},
        micro_candidate_filter={"cost_to_target_ratio": 0.45, "critical_window_coverage": 22.0},
    )

    assert "BUY_TRADE_RATIO_LOW" in result["block_reasons"]
    assert "MICRO_STATE_WEAK" in result["block_reasons"]
    assert result["primary_block_reason"] in result["block_reasons"]
    assert result["gate_values"]["buy_trade_ratio_5s"] == 0.48


def test_gate_diagnostics_summary_counts_reasons():
    summary = summarize_gate_diagnostics([{"primary_block_reason": "BUY_TRADE_RATIO_LOW", "block_reasons": ["BUY_TRADE_RATIO_LOW"]}])

    assert summary["candidate_count"] == 1
    assert summary["primary_block_reason_counts"]["BUY_TRADE_RATIO_LOW"] == 1
