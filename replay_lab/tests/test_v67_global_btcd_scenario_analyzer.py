from __future__ import annotations

from analysis.v67_global_btcd_scenario_analyzer import analyze_v67_global_btcd_scenarios


def test_v67_scenario_analyzer_requires_global_history(tmp_path):
    summary = analyze_v67_global_btcd_scenarios([], 500000, reports_dir=tmp_path, archive_dir=tmp_path, history_path=tmp_path / "missing.csv")
    assert summary["full_period_validation_possible"] is False
    assert summary["scenarios"][1]["decision"] == "GLOBAL_BTCD_DATA_REQUIRED"
