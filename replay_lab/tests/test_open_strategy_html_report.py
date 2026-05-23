import json

from replay_lab.feedback.open_strategy_html_report import OpenStrategyHTMLReportBuilder


def test_open_strategy_html_report_generates_sections(tmp_path):
    report = tmp_path / "reports" / "open_strategy"
    report.mkdir(parents=True)
    (report / "external_strategy_registry.json").write_text(json.dumps({"source_count": 5, "strategy_specs_created": 7, "license_review_required_count": 1, "do_not_use_count": 0, "strategies": []}), encoding="utf-8")
    (report / "external_strategy_lab.json").write_text(json.dumps({"accepted_strategy_count": 0, "strategy_results": [{"strategy_id": "s1", "strategy_name": "VWAP Pullback Scalp", "strategy_family": "scalp", "enter_count": 3, "pf_realistic_1": 0.8, "expectancy_realistic_1": -0.01, "survives_cost": False}]}), encoding="utf-8")

    path = OpenStrategyHTMLReportBuilder(store_dir=tmp_path, docs_root=tmp_path / "docs").build()

    html = path.read_text(encoding="utf-8")
    assert "외부 전략 검증 결과" in html
    assert "살아남은 전략" in html
    assert "폐기 또는 추가 검증 전략" in html
    assert (tmp_path / "docs" / "latest_open_strategy_report.html").exists()
