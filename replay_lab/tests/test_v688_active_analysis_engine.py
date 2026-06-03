from __future__ import annotations

from active_analysis.active_analysis_engine import run_active_analysis_engine
from active_analysis.recommendation_scoring import recommendation


def test_v688_active_analysis_forbids_auto_actions(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    payload = run_active_analysis_engine(reports_dir=reports, data_dir=tmp_path / "data")
    assert payload["active_change_applied"] is False
    assert payload["live_order_allowed"] is False
    assert all(row["allowed_action"] != "AUTO_ACTIVE_CHANGE" for row in payload["recommendations"])
    assert (reports / "latest_v688_active_analysis_recommendations_report.html").exists()


def test_v688_recommendation_rejects_forbidden_actions() -> None:
    try:
        recommendation("bad", "t", "HIGH", 1.0, "none", allowed_action="AUTO_ACTIVE_CHANGE")
    except ValueError:
        return
    raise AssertionError("AUTO_ACTIVE_CHANGE should be rejected")
