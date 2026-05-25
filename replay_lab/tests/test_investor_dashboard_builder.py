from __future__ import annotations

import json

from replay_lab.research.investor_dashboard_builder import build_investor_dashboard


def test_investor_dashboard_is_korean_utf8_entrypoint(tmp_path):
    reports = tmp_path / "docs/reports"
    reports.mkdir(parents=True)
    (reports / "latest_true_walk_forward_summary.json").write_text(
        json.dumps(
            {
                "investment_start_time": "2025-01-01",
                "investment_end_time": "2026-01-01",
                "capital": {
                    "final_equity_krw": 550000,
                    "total_return_pct": 10.0,
                    "max_drawdown_pct": -4.0,
                    "trade_count": 12,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (reports / "latest_v64_return_amplification_report.html").write_text("<html></html>", encoding="utf-8")
    (reports / "latest_future_alpha_report.html").write_text("<html></html>", encoding="utf-8")

    result = build_investor_dashboard(str(reports))
    html = (reports / "astt_report_dashboard.html").read_text(encoding="utf-8")

    assert result["source"] == "latest_true_walk_forward_summary.json"
    assert "ASTT Report Dashboard" in html
    assert "V6.4 수익률 확대 실험" in html
    assert "latest_v64_return_amplification_report.html" in html
    assert "latest_future_alpha_report.html" in html
    assert "전체 리포트 목록" in html
    assert "계좌 평가금(Equity)" in html
    assert "가격 공백 구간(FVG)" in html
    assert "占" not in html
