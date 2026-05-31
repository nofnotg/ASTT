from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v684_bear_windows_analyzer import run_v684_bear_windows
from analysis.v684_indicator_effectiveness_lab import run_v684_indicator_effectiveness_lab
from analysis.v684_loss_guard_indicator_lab import run_v684_loss_guard_indicator_lab
from replay_lab.feedback.v684_reports_html import V684ReportsHTML


def build_v684_bear_windows_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v684_bear_windows(initial_cash_krw, reports_dir)
    V684ReportsHTML(reports_dir).build_bear_windows()
    return payload


def run_v684_indicator_effectiveness(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v684_indicator_effectiveness_lab(initial_cash_krw, reports_dir)
    V684ReportsHTML(reports_dir).build_indicator_effectiveness()
    return payload


def run_v684_loss_guard_indicator(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v684_loss_guard_indicator_lab(initial_cash_krw, reports_dir)
    V684ReportsHTML(reports_dir).build_loss_guard_indicator()
    return payload


def build_v684_bear_windows_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V684ReportsHTML(reports_dir).build_bear_windows()


def build_v684_indicator_effectiveness_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V684ReportsHTML(reports_dir).build_indicator_effectiveness()


def build_v684_loss_guard_indicator_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V684ReportsHTML(reports_dir).build_loss_guard_indicator()


def build_v684_dashboard_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V684ReportsHTML(reports_dir).build_dashboard()
