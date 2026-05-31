from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v682_bear_response_analyzer import (
    analyze_v682_bear_bounce_profit,
    analyze_v682_bear_defense_deep_insight,
    analyze_v682_bear_response_router,
    build_v682_bounce_case_study,
    register_v682_shadow_route,
)
from replay_lab.feedback.v682_reports_html import V682ReportsHTML


def run_v682_bear_defense_deep_insight_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v682_bear_defense_deep_insight(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v682_bear_defense_insight_summary.json", payload)
    V682ReportsHTML(reports_dir).build_bear_defense_insight()
    return payload


def run_v682_bear_bounce_profit_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v682_bear_bounce_profit(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v682_bear_bounce_summary.json", payload)
    V682ReportsHTML(reports_dir).build_bear_bounce()
    return payload


def run_v682_bear_response_router_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v682_bear_response_router(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v682_bear_response_router_summary.json", payload)
    V682ReportsHTML(reports_dir).build_bear_response_router()
    return payload


def build_v682_bounce_case_study_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v682_bounce_case_study(reports_dir)
    _write(Path(reports_dir) / "latest_v682_bounce_case_study_summary.json", payload)
    V682ReportsHTML(reports_dir).build_bounce_case_study()
    return payload


def register_v682_bear_shadow_route_lab(route: str, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = register_v682_shadow_route(route, reports_dir)
    _write(Path(reports_dir) / f"latest_v682_{route.lower()}_shadow_registration_summary.json", payload)
    return payload


def build_v682_bear_defense_insight_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V682ReportsHTML(reports_dir).build_bear_defense_insight()


def build_v682_bear_bounce_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V682ReportsHTML(reports_dir).build_bear_bounce()


def build_v682_bear_response_router_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V682ReportsHTML(reports_dir).build_bear_response_router()


def build_v682_bounce_case_study_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    return V682ReportsHTML(reports_dir).build_bounce_case_study()


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
