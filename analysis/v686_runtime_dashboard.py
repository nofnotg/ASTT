from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v686_core import (
    build_v686_active_shadow_runtime_payload,
    build_v686_control_tower_dashboard_payload,
    build_v686_local_dashboard_payload,
    build_v686_shadow_route_registration_payload,
    persist_payload,
)


def register_v686_shadow_routes(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return persist_payload("latest_v686_shadow_route_registration_summary.json", build_v686_shadow_route_registration_payload(reports_dir), reports_dir)


def run_v686_paper_backfill_with_v685_router(initial_cash_krw: float = 500000.0, start_date: str = "2026-01-01", reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return persist_payload("latest_v686_active_shadow_runtime_summary.json", build_v686_active_shadow_runtime_payload(initial_cash_krw, start_date, reports_dir), reports_dir)


def build_v686_active_shadow_dashboard_data(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    path = Path(reports_dir) / "latest_v686_active_shadow_runtime_summary.json"
    return persist_payload("latest_v686_active_shadow_runtime_summary.json", __import__("json").loads(path.read_text(encoding="utf-8-sig")) if path.exists() else build_v686_active_shadow_runtime_payload(reports_dir=reports_dir), reports_dir)


def build_v686_local_dashboard_summary(host: str = "127.0.0.1", port: int = 8787, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return persist_payload("latest_v686_local_dashboard_summary.json", build_v686_local_dashboard_payload(host, port, reports_dir), reports_dir)


def run_v686_control_tower_dashboard_review(reports_dir: str | Path = "docs/reports", llm_provider: str = "openai") -> dict[str, Any]:
    return persist_payload("latest_v686_control_tower_dashboard_summary.json", build_v686_control_tower_dashboard_payload(reports_dir, llm_provider), reports_dir)
