from __future__ import annotations

from typing import Any

from analysis.v684_risk_sizing_lab import run_v684_risk_sizing_lab
from replay_lab.feedback.v684_reports_html import V684ReportsHTML


def run_v684_risk_sizing(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v684_risk_sizing_lab(initial_cash_krw, reports_dir)
    V684ReportsHTML(reports_dir).build_risk_sizing()
    return payload


def build_v684_risk_sizing_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V684ReportsHTML(reports_dir).build_risk_sizing()
