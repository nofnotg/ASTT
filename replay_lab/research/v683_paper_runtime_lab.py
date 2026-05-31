from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v683_paper_runtime_analyzer import (
    build_v683_active_shadow_comparison,
    build_v683_route_router_report,
    check_v683_paper_health,
    run_v683_control_tower_review,
    run_v683_paper_backfill_from_20260101,
    start_v683_live_forward_paper,
    switch_v683_active_paper_route,
)
from replay_lab.feedback.v683_reports_html import V683ReportsHTML


def run_v683_paper_backfill_lab(initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01", reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v683_paper_backfill_from_20260101(initial_cash_krw, start_date, reports_dir)
    _write(Path(reports_dir) / "latest_v683_backfill_20260101_summary.json", payload)
    runtime = {
        "schema_version": "v683_paper_runtime_v1",
        "active_route": payload["active_route"],
        "shadow_routes": payload["shadow_routes"],
        "current_equity_krw": next(row["final_equity_krw"] for row in payload["routes"] if row["route_status"] == "ACTIVE"),
        "current_cash_krw": next(row["final_equity_krw"] for row in payload["routes"] if row["route_status"] == "ACTIVE"),
        "open_positions": 0,
        "start_date": start_date,
        "healthcheck": "PAPER_BACKFILL_READY",
        "decision": "PAPER_RUNNING",
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v683_paper_runtime_summary.json", runtime)
    html = V683ReportsHTML(reports_dir)
    html.build_backfill()
    html.build_runtime()
    html.build_period_reports()
    return payload


def start_v683_live_forward_paper_lab(active_route: str = "LG_V2_BALANCED_PLUS_DOM_GATE", port: int = 8787, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = start_v683_live_forward_paper(active_route, port, reports_dir)
    _write(Path(reports_dir) / "latest_v683_paper_runtime_summary.json", payload)
    V683ReportsHTML(reports_dir).build_runtime()
    return payload


def check_v683_paper_health_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = check_v683_paper_health(reports_dir)
    _write(Path(reports_dir) / "latest_v683_paper_health_summary.json", payload)
    return payload


def build_v683_active_shadow_comparison_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v683_active_shadow_comparison(reports_dir)
    _write(Path(reports_dir) / "latest_v683_active_shadow_comparison_summary.json", payload)
    V683ReportsHTML(reports_dir).build_active_shadow()
    return payload


def build_v683_route_router_report_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v683_route_router_report(reports_dir)
    _write(Path(reports_dir) / "latest_v683_route_router_summary.json", payload)
    V683ReportsHTML(reports_dir).build_router()
    return payload


def run_v683_control_tower_review_lab(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    payload = run_v683_control_tower_review(reports_dir, llm_provider)
    _write(Path(reports_dir) / "latest_v683_control_tower_summary.json", payload)
    V683ReportsHTML(reports_dir).build_control_tower()
    return payload


def build_v683_paper_dashboard_html_lab(reports_dir: str = "docs/reports") -> dict[str, str]:
    html = V683ReportsHTML(reports_dir)
    html.build_period_reports()
    return html.build_dashboard()


def register_v683_shadow_route_lab(route: str, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = {
        "schema_version": "v683_shadow_route_registration_v1",
        "route": route,
        "status": "SHADOW",
        "registered": True,
        "active_change_applied": False,
        "decision": "PAPER_ROUTE_SHADOW",
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / f"latest_v683_{route.lower()}_shadow_registration_summary.json", payload)
    return payload


def switch_v683_active_paper_route_lab(route: str, confirm_switch: bool = False, reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = switch_v683_active_paper_route(route, confirm_switch)
    _write(Path(reports_dir) / "latest_v683_route_switch_summary.json", payload)
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
