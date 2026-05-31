from __future__ import annotations

import json

from replay_lab.feedback.v685_reports_html import V685ReportsHTML


def test_v685_reports_render_expected_links(tmp_path) -> None:
    reports = tmp_path
    (reports / "latest_v685_atr_precision_audit_summary.json").write_text(json.dumps({"decision": "ATR_RESEARCH_ONLY", "scenarios": []}), encoding="utf-8")
    (reports / "latest_v685_atr_price_path_audit_summary.json").write_text(json.dumps({"final_atr_decision": "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED", "lower_timeframe": {}, "fill_model_results": [], "audit_rows": []}), encoding="utf-8")
    (reports / "latest_v685_atr_sensitivity_summary.json").write_text(json.dumps({"overfit_warning": "warn", "rows": []}), encoding="utf-8")
    (reports / "latest_v685_bear_window_classification_summary.json").write_text(json.dumps({"windows": []}), encoding="utf-8")
    (reports / "latest_v685_bear_window_performance_summary.json").write_text(json.dumps({"window_rows": [], "scenario_rows": [], "window_type_summary": []}), encoding="utf-8")
    (reports / "latest_v685_bear_router_window_aware_summary.json").write_text(json.dumps({"decision": "BEAR_ROUTER_NEEDS_FORWARD_PAPER", "rows": [], "route_rules": []}), encoding="utf-8")
    html = V685ReportsHTML(str(reports))
    html.build_atr_precision()
    html.build_atr_price_path()
    html.build_atr_sensitivity()
    html.build_bear_window_classification()
    html.build_bear_window_performance()
    html.build_bear_router_window_aware()
    html.build_dashboard()
    assert (reports / "latest_v685_bear_router_window_aware_report.html").exists()
    assert "V6.8.5 ATR Precision + Bear Window Performance" in (reports / "astt_report_dashboard.html").read_text(encoding="utf-8")
