from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v681_compounding_control_tower import (
    ACTIVE_ROUTE,
    analyze_v681_bear_compounding_agents,
    analyze_v681_compounding_dominance,
    analyze_v681_compounding_router,
    audit_v681_compounding_vs_dominance_ledger,
    build_v681_control_tower_review,
    register_v681_shadow_route,
    run_v681_paper_backfill_from_20260101,
    start_v681_paper_server,
)
from replay_lab.feedback.v681_reports_html import V681ReportsHTML


def audit_v681_compounding_vs_dominance_ledger_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = audit_v681_compounding_vs_dominance_ledger(reports_dir)
    _write(Path(reports_dir) / "latest_v681_reconciliation_audit_summary.json", payload)
    V681ReportsHTML(reports_dir).build_reconciliation()
    return payload


def run_v681_compounding_dominance_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v681_compounding_dominance(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v681_compounding_dominance_summary.json", payload)
    V681ReportsHTML(reports_dir).build_compounding_dominance()
    return payload


def run_v681_bear_compounding_agent_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v681_bear_compounding_agents(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v681_bear_compounding_agent_summary.json", payload)
    V681ReportsHTML(reports_dir).build_bear_agent()
    return payload


def run_v681_compounding_scenario_router_lab(initial_cash_krw: float = 500000.0, use_available_history: bool = True, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = analyze_v681_compounding_router(initial_cash_krw, reports_dir)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v681_compounding_router_summary.json", payload)
    V681ReportsHTML(reports_dir).build_router()
    return payload


def run_v681_control_tower_review_lab(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    payload = build_v681_control_tower_review(reports_dir, llm_provider)
    _write(Path(reports_dir) / "latest_v681_control_tower_summary.json", payload)
    V681ReportsHTML(reports_dir).build_control_tower()
    return payload


def run_v681_paper_backfill_lab(initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01", active_route: str = ACTIVE_ROUTE, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v681_paper_backfill_from_20260101(initial_cash_krw, start_date, active_route, reports_dir)
    _write(Path(reports_dir) / "latest_v681_paper_runtime_summary.json", payload)
    V681ReportsHTML(reports_dir).build_paper_runtime()
    return payload


def start_v681_paper_server_lab(active_route: str = ACTIVE_ROUTE, port: int = 8787, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = start_v681_paper_server(active_route, port, reports_dir)
    _write(Path(reports_dir) / "latest_v681_paper_runtime_summary.json", payload)
    V681ReportsHTML(reports_dir).build_paper_runtime()
    return payload


def register_v681_shadow_route_lab(route: str, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = register_v681_shadow_route(route, reports_dir)
    _write(Path(reports_dir) / "latest_v681_paper_runtime_summary.json", payload)
    V681ReportsHTML(reports_dir).build_paper_runtime()
    return payload


def build_v681_integrated_investment_report_html(reports_dir: str = "docs/reports") -> dict[str, str]:
    from replay_lab.feedback.v62_full_investment_report_html import V62FullInvestmentReportHTML

    return V62FullInvestmentReportHTML().build(reports_dir)


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
