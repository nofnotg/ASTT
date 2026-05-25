from replay_lab.research.v65_ma_scenario_comparison import build_v65_ma_risk_report


def test_v65_ma_risk_report_defaults_without_inputs(tmp_path) -> None:
    summary = build_v65_ma_risk_report(str(tmp_path))
    assert summary["real_order_enabled"] is False
    assert summary["live_order_allowed"] is False
