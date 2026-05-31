from __future__ import annotations

from typing import Any

from analysis.v686_runtime_dashboard import (
    build_v686_active_shadow_dashboard_data,
    build_v686_local_dashboard_summary,
    register_v686_shadow_routes,
    run_v686_control_tower_dashboard_review,
    run_v686_paper_backfill_with_v685_router,
)
from local_dashboard.dashboard_health_service import check_dashboard_health
from replay_lab.feedback.v686_reports_html import V686ReportsHTML


def register_v686_shadow_routes_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    return register_v686_shadow_routes(reports_dir)


def run_v686_paper_backfill_with_v685_router_lab(initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01", reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = run_v686_paper_backfill_with_v685_router(initial_cash_krw, start_date, reports_dir)
    V686ReportsHTML(reports_dir).build_active_shadow_runtime()
    return payload


def build_v686_active_shadow_dashboard_data_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    payload = build_v686_active_shadow_dashboard_data(reports_dir)
    V686ReportsHTML(reports_dir).build_active_shadow_runtime()
    return payload


def build_v686_local_dashboard_report_html(reports_dir: str = "docs/reports", host: str = "127.0.0.1", port: int = 8787) -> dict[str, str]:
    build_v686_local_dashboard_summary(host, port, reports_dir)
    html = V686ReportsHTML(reports_dir)
    html.build_local_dashboard()
    html.build_dashboard()
    return {"html": str(__import__("pathlib").Path(reports_dir) / "latest_v686_local_dashboard_report.html")}


def check_v686_local_dashboard_health_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    return check_dashboard_health(reports_dir)


def run_v686_control_tower_dashboard_review_lab(reports_dir: str = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    payload = run_v686_control_tower_dashboard_review(reports_dir, llm_provider)
    V686ReportsHTML(reports_dir).build_control_tower_dashboard()
    return payload
