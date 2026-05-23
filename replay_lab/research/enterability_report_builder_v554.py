from __future__ import annotations

from replay_lab.feedback.micro_entry_diagnostics_html_report import MicroEntryDiagnosticsHTMLReportBuilder


def build_enterability_report_v554() -> dict:
    path = MicroEntryDiagnosticsHTMLReportBuilder().build()
    return {"report_path": str(path)}
