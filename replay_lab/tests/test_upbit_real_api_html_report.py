import json

from replay_lab.feedback.upbit_real_api_html_report import UpbitRealAPIHTMLReportBuilder


def test_upbit_real_api_html_report_generates_latest_files(tmp_path):
    ws = tmp_path / "sessions" / "upbit_ws" / "s1"
    ws.mkdir(parents=True)
    (ws / "session_summary.json").write_text(json.dumps({"data_source": "UPBIT_WS", "trade_event_count": 1, "orderbook_event_count": 1, "eligible_for_live_readiness": True}), encoding="utf-8")
    report = tmp_path / "reports" / "upbit_real_api"
    report.mkdir(parents=True)
    (report / "candidate_second_window_validation.json").write_text(json.dumps({"good_window_count": 1, "partial_window_count": 0, "profit_factor_realistic_1": 1.2, "expectancy_realistic_1": 0.01}), encoding="utf-8")

    path = UpbitRealAPIHTMLReportBuilder(store_dir=tmp_path, docs_root=tmp_path / "docs").build()

    html = path.read_text(encoding="utf-8")
    assert "실제 업비트 데이터인가" in html
    assert "Candidate-window 초봉" in html
    assert (tmp_path / "docs" / "latest_upbit_real_api_report.html").exists()
