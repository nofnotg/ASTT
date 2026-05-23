import json

from replay_lab.feedback.realistic_paper_html_report_v555 import RealisticPaperHTMLReportV555


def test_realistic_paper_html_report_v555_generates_latest(tmp_path):
    session = tmp_path / "sessions" / "realistic_paper_v555" / "s1"
    session.mkdir(parents=True)
    (session / "session_summary.json").write_text(json.dumps({"session_id": "s1", "duration_minutes": 1, "initial_cash_krw": 500000, "final_equity_krw": 500000, "total_pnl_krw": 0, "candidate_count": 0, "enter_count": 0, "trade_count": 0, "profit_factor": 0.0, "source_counts": {}}), encoding="utf-8")
    path = RealisticPaperHTMLReportV555(store_dir=tmp_path, docs_root=tmp_path / "docs").build(tmp_path / "sessions" / "realistic_paper_v555")
    html = path.read_text(encoding="utf-8")
    assert "Realistic Paper Execution Ledger" in html
    assert "후보 source별 결과" in html
    assert (tmp_path / "docs" / "latest_realistic_paper_report.html").exists()
