from __future__ import annotations

from active_analysis.v688_dashboard_builder import build_v688_control_tower_dashboard_data


def test_v688_dashboard_data_has_required_tabs(tmp_path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    payload = build_v688_control_tower_dashboard_data(reports)
    assert payload["tabs"]["scenario_telemetry_tab"] is True
    assert payload["tabs"]["llm_council_tab"] is True
    assert (reports / "astt_report_dashboard.html").exists()
