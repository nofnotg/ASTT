from __future__ import annotations

from replay_lab.feedback.open_strategy_html_report import OpenStrategyHTMLReportBuilder


def build_open_strategy_report() -> dict:
    path = OpenStrategyHTMLReportBuilder().build()
    return {"report_path": str(path)}
