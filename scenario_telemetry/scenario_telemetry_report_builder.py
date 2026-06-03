from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.scenario_daily_stats import build_scenario_telemetry
from scenario_telemetry.v688_common import read_json, write_html


def build_scenario_telemetry_report(reports_dir: str | Path = "docs/reports") -> str:
    reports = Path(reports_dir)
    if not (reports / "latest_v688_scenario_daily_summary.json").exists():
        build_scenario_telemetry(reports_dir=reports)
    daily = read_json(reports / "latest_v688_scenario_daily_summary.json")
    weekly = read_json(reports / "latest_v688_scenario_weekly_summary.json")
    monthly = read_json(reports / "latest_v688_scenario_monthly_summary.json")
    return write_html(
        reports / "latest_v688_scenario_telemetry_report.html",
        "V6.8.8 Scenario Telemetry",
        [
            ("Daily Scenario Stats", daily.get("rows", [])),
            ("Weekly Scenario Stats", weekly.get("rows", [])),
            ("Monthly Scenario Stats", monthly.get("rows", [])),
            ("Safety", _safety(daily)),
        ],
    )


def _safety(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload.get(key) for key in ("real_order_enabled", "live_order_allowed", "auto_apply_allowed", "manual_review_required")}
