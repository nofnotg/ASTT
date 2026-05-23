import json

from replay_lab.feedback.micro_entry_diagnostics_html_report import MicroEntryDiagnosticsHTMLReportBuilder


def test_micro_entry_diagnostics_html_report_contains_required_sections(tmp_path):
    report = tmp_path / "reports" / "micro_entry_diagnostics"
    report.mkdir(parents=True)
    (report / "gate_diagnostics_v554.json").write_text(json.dumps({"candidate_count": 35, "ENTER_count": 0, "good_partial_count": 18, "primary_block_reason_counts": {"MICRO_STATE_WEAK": 17}, "block_reason_table": [{"block_reason": "MICRO_STATE_WEAK", "count": 17, "pct": 48.6}]}), encoding="utf-8")
    (report / "gate_abtest_v554.json").write_text(json.dumps({"profiles": {"STRICT": {"candidate_count": 35, "enter_count": 0, "wait_count": 17, "cancel_count": 1, "pf_realistic_1": 0.0, "research_only": False}}}), encoding="utf-8")
    (report / "priority_external_strategy_ws_v554.json").write_text(json.dumps({"strategy_results": []}), encoding="utf-8")

    path = MicroEntryDiagnosticsHTMLReportBuilder(store_dir=tmp_path, docs_root=tmp_path / "docs").build()

    html = path.read_text(encoding="utf-8")
    assert "ENTER를 막은 조건 TOP" in html
    assert "STRICT / BALANCED / EXPLORATORY 비교" in html
    assert "실제 WS forward session 결과" in html
    assert (tmp_path / "docs" / "latest_micro_entry_diagnostics_report.html").exists()
