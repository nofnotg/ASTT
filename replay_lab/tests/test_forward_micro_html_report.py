from execution.forward_paper_micro_runner import run_forward_paper_micro_session
from replay_lab.feedback.forward_micro_html_report import ForwardMicroHTMLReportBuilder


def test_forward_micro_html_report_generates_latest_files(tmp_path, monkeypatch):
    monkeypatch.setattr("execution.forward_paper_micro_runner.REPLAY_STORE_DIR", tmp_path)
    run_forward_paper_micro_session(duration_minutes=1, markets=["KRW-BTC"], top_markets=1)
    docs = tmp_path / "docs"

    path = ForwardMicroHTMLReportBuilder(store_dir=tmp_path, docs_root=docs).build(tmp_path / "sessions" / "live_micro")

    html = path.read_text(encoding="utf-8")
    assert "PAPER forward" in html
    assert "0.05% 비용" in html
    assert (docs / "latest_forward_micro_report.html").exists()
