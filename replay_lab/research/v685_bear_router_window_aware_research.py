from __future__ import annotations

from typing import Any

from analysis.v685_bear_router_window_aware_lab import run_v685_bear_router_window_aware_lab
from replay_lab.feedback.v685_reports_html import V685ReportsHTML


def run_v685_bear_router_window_aware(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_bear_router_window_aware_lab(initial_cash_krw, reports_dir)
    html = V685ReportsHTML(reports_dir)
    html.build_bear_router_window_aware()
    html.build_dashboard()
    return payload


def build_v685_bear_router_window_aware_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_bear_router_window_aware()
