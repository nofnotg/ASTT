from __future__ import annotations

from typing import Any

from analysis.v685_bear_window_classification import run_v685_bear_window_classification
from analysis.v685_bear_window_performance_lab import run_v685_bear_window_performance_lab
from replay_lab.feedback.v685_reports_html import V685ReportsHTML


def build_v685_bear_window_classification(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_bear_window_classification(initial_cash_krw, reports_dir)
    V685ReportsHTML(reports_dir).build_bear_window_classification()
    return payload


def run_v685_bear_window_performance(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_bear_window_performance_lab(initial_cash_krw, reports_dir)
    V685ReportsHTML(reports_dir).build_bear_window_performance()
    return payload


def build_v685_bear_window_classification_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_bear_window_classification()


def build_v685_bear_window_performance_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_bear_window_performance()
