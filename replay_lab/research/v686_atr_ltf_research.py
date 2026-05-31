from __future__ import annotations

from typing import Any

from analysis.v686_atr_ltf_coverage import run_v686_atr_ltf_coverage
from analysis.v686_atr_ltf_replay import run_v686_atr_ltf_replay
from analysis.v686_atr_precision_v2 import run_v686_atr_precision_v2
from analysis.v686_bear_window_atr_replay import run_v686_bear_window_atr_replay
from replay_lab.feedback.v686_reports_html import V686ReportsHTML


def run_v686_atr_ltf_coverage_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v686_atr_ltf_coverage(initial_cash_krw, reports_dir)
    V686ReportsHTML(reports_dir).build_atr_ltf_coverage()
    return payload


def run_v686_atr_ltf_replay_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v686_atr_ltf_replay(initial_cash_krw, reports_dir)
    V686ReportsHTML(reports_dir).build_atr_ltf_replay()
    return payload


def run_v686_atr_precision_v2_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v686_atr_precision_v2(initial_cash_krw, reports_dir)
    html = V686ReportsHTML(reports_dir)
    html.build_atr_precision_v2()
    html.build_atr_model_comparison()
    return payload


def run_v686_bear_window_atr_replay_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v686_bear_window_atr_replay(initial_cash_krw, reports_dir)
    V686ReportsHTML(reports_dir).build_bear_window_atr_replay()
    return payload


def build_v686_atr_ltf_coverage_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V686ReportsHTML(reports_dir).build_atr_ltf_coverage()


def build_v686_atr_ltf_replay_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V686ReportsHTML(reports_dir).build_atr_ltf_replay()


def build_v686_atr_precision_v2_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V686ReportsHTML(reports_dir).build_atr_precision_v2()


def build_v686_atr_model_comparison_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V686ReportsHTML(reports_dir).build_atr_model_comparison()


def build_v686_bear_window_atr_replay_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V686ReportsHTML(reports_dir).build_bear_window_atr_replay()
