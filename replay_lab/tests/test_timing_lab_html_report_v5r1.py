from replay_lab.feedback.timing_lab_html_report_v5r1 import TimingLabHTMLReportV5R1


def test_timing_lab_html_report_generates_event_clip_state_table_files(tmp_path):
    summary = TimingLabHTMLReportV5R1().build(tmp_path)
    assert summary["real_order_enabled"] is False
    assert (tmp_path / "latest_timing_lab_report.html").exists()
