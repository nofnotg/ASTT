from __future__ import annotations

from datetime import date
from pathlib import Path

from replay_lab.feedback.micro_execution_html_report import MicroExecutionHTMLReportBuilder


def build_micro_response_report(start_date: date, end_date: date) -> Path:
    return MicroExecutionHTMLReportBuilder().build(start_date=start_date.isoformat(), end_date=end_date.isoformat())
