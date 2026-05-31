from __future__ import annotations

import json

from replay_lab.feedback.v684_reports_html import V684ReportsHTML


def test_v684_reports_render_expected_links(tmp_path) -> None:
    reports = tmp_path
    (reports / "latest_v684_bear_windows_summary.json").write_text(json.dumps({"decision": "BEAR_WINDOWS_READY", "window_count": 1, "windows": []}), encoding="utf-8")
    (reports / "latest_v684_indicator_effectiveness_summary.json").write_text(json.dumps({"indicators": []}), encoding="utf-8")
    (reports / "latest_v684_loss_guard_indicator_lab_summary.json").write_text(json.dumps({"scenarios": []}), encoding="utf-8")
    (reports / "latest_v684_bear_bounce_v3_summary.json").write_text(json.dumps({"scenario": {}, "bounce_types": []}), encoding="utf-8")
    (reports / "latest_v684_risk_sizing_lab_summary.json").write_text(json.dumps({"models": []}), encoding="utf-8")
    (reports / "latest_v684_bear_router_summary.json").write_text(json.dumps({"decision": "BEAR_ROUTER_CANDIDATE", "scenarios": [], "routing_rules": []}), encoding="utf-8")
    html = V684ReportsHTML(str(reports))
    html.build_bear_windows()
    html.build_indicator_effectiveness()
    html.build_loss_guard_indicator()
    html.build_bear_bounce_v3()
    html.build_risk_sizing()
    html.build_bear_router()
    html.build_dashboard()
    assert (reports / "latest_v684_bear_router_report.html").exists()
    assert "V6.8.4 Bear Indicator Validation" in (reports / "astt_report_dashboard.html").read_text(encoding="utf-8")
