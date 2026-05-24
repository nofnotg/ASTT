from pathlib import Path

from replay_lab.feedback.winner_trace_html_report_v558 import WinnerTraceHTMLReportV558


def test_winner_trace_html_report_generates_latest():
    path = WinnerTraceHTMLReportV558().build()
    assert path.exists()
    assert Path("docs/reports/latest_winner_trace_summary.json").exists()
