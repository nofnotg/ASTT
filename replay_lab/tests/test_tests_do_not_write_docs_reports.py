import hashlib
from pathlib import Path

from replay_lab.feedback.entry_discovery_html_report_v556 import EntryDiscoveryHTMLReportV556


def test_report_builder_test_output_does_not_write_docs_reports(tmp_path):
    target = Path("docs/reports/latest_entry_discovery_summary.json")
    before = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else ""
    session = tmp_path / "s1"
    session.mkdir()
    (session / "ledger.jsonl").write_text("", encoding="utf-8")
    EntryDiscoveryHTMLReportV556().build(tmp_path, docs_output_dir=tmp_path / "docs", replay_output_dir=tmp_path / "replay", generated_by="TEST", is_test_artifact=True)
    after = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else ""
    assert before == after
