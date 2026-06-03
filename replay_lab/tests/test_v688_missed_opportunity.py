from __future__ import annotations

from scenario_telemetry.scenario_counterfactual import build_missed_opportunity_analysis


def test_v688_missed_opportunity_is_manual_review_only(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    payload = build_missed_opportunity_analysis(reports_dir=reports, data_dir=tmp_path / "data")
    assert payload["active_change_applied"] is False
    assert payload["manual_review_required"] is True
    assert (reports / "latest_v688_missed_opportunity_report.html").exists()
