from __future__ import annotations

from typing import Any

from analysis.v685_atr_precision_audit import run_v685_atr_precision_audit
from analysis.v685_atr_price_path_audit import run_v685_atr_price_path_audit
from analysis.v685_atr_sensitivity_lab import run_v685_atr_sensitivity_lab
from replay_lab.feedback.v685_reports_html import V685ReportsHTML


def run_v685_atr_precision(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_atr_precision_audit(initial_cash_krw, reports_dir)
    V685ReportsHTML(reports_dir).build_atr_precision()
    return payload


def run_v685_atr_price_path(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_atr_price_path_audit(initial_cash_krw, reports_dir)
    V685ReportsHTML(reports_dir).build_atr_price_path()
    return payload


def run_v685_atr_sensitivity(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v685_atr_sensitivity_lab(initial_cash_krw, reports_dir)
    V685ReportsHTML(reports_dir).build_atr_sensitivity()
    return payload


def build_v685_atr_precision_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_atr_precision()


def build_v685_atr_price_path_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_atr_price_path()


def build_v685_atr_sensitivity_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V685ReportsHTML(reports_dir).build_atr_sensitivity()
