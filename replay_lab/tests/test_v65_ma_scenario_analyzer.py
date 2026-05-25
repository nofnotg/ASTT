from analysis.v65_ma_scenario_analyzer import analyze_v65_ma_scenarios


def test_v65_ma_scenario_analyzer_handles_empty_journal() -> None:
    summary = analyze_v65_ma_scenarios([], 500000, "missing")
    assert len(summary["scenarios"]) == 6
    assert summary["audit"]["fail"] == 0
    assert summary["real_order_enabled"] is False
