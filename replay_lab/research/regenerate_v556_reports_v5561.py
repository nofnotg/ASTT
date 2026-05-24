from __future__ import annotations

from pathlib import Path

from replay_lab.feedback.entry_discovery_html_report_v556 import EntryDiscoveryHTMLReportV556
from replay_lab.feedback.head_controller_html_report_v556 import HeadControllerHTMLReportV556
from replay_lab.research.artifact_integrity_check_v5561 import check_artifact_integrity_v5561


def regenerate_v556_production_reports_v5561(sessions_dir: str | Path) -> dict:
    entry = EntryDiscoveryHTMLReportV556().build(sessions_dir, generated_by="CLI", is_test_artifact=False)
    head = HeadControllerHTMLReportV556().build("docs/reports", "off", None)
    integrity = check_artifact_integrity_v5561("docs/reports")
    return {"entry_discovery_report": str(entry), "head_controller_report": str(head), "artifact_integrity": integrity}
