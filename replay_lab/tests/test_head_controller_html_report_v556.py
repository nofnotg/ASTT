from replay_lab.feedback.head_controller_html_report_v556 import HeadControllerHTMLReportV556


def test_head_controller_report_generates(tmp_path):
    out = HeadControllerHTMLReportV556().build(tmp_path, docs_output_dir=tmp_path / "docs", replay_output_dir=tmp_path / "replay")
    assert out.exists()
