import json

from replay_lab.feedback.v65_ma_scenario_report_html import V65MAScenarioReportHTML


def test_v65_ma_report_contains_korean_safety_text(tmp_path) -> None:
    payload = {
        "scenarios": [{"scenario": "CONTROL_CURRENT_ROUTER", "final_equity_krw": 500000, "total_return_pct": 0, "mdd_pct": 0, "profit_factor": 1, "trade_count": 0}],
        "recommendation": {"best_scenario": "CONTROL_CURRENT_ROUTER", "final_judgement": "LIVE_NOT_ALLOWED"},
        "audit": {"fail": 0},
    }
    (tmp_path / "latest_v65_ma_scenario_summary.json").write_text(json.dumps(payload), encoding="utf-8")
    result = V65MAScenarioReportHTML(str(tmp_path)).build()
    html = (tmp_path / "latest_v65_ma_scenario_report.html").read_text(encoding="utf-8")
    assert "MA는 매수 버튼이 아닙니다" in html
    assert "실제 주문" in html
    assert result["html"].endswith(".html")
