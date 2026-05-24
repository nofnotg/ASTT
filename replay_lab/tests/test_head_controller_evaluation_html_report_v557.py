from replay_lab.feedback.head_controller_evaluation_html_report_v557 import HeadControllerEvaluationHTMLReportV557


def test_head_controller_evaluation_html_report_writes_latest():
    path = HeadControllerEvaluationHTMLReportV557().build("docs/reports", "openai")
    assert path.exists()
    assert path.name == "latest_head_controller_evaluation_report.html"
