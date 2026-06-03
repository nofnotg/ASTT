from __future__ import annotations

from pathlib import Path
from typing import Any

from llm_council.llm_review_report_builder import build_llm_review_report
from scenario_telemetry.scenario_telemetry_report_builder import build_scenario_telemetry_report
from scenario_telemetry.v688_common import read_json, safe_status, write_html, write_json


def build_v688_control_tower_dashboard_data(reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    reports = Path(reports_dir)
    payload = {
        "schema_version": "v688_control_tower_dashboard_v1",
        "scenario_genome": read_json(reports / "latest_v688_scenario_genome_summary.json"),
        "scenario_daily": read_json(reports / "latest_v688_scenario_daily_summary.json"),
        "scenario_weekly": read_json(reports / "latest_v688_scenario_weekly_summary.json"),
        "scenario_monthly": read_json(reports / "latest_v688_scenario_monthly_summary.json"),
        "disagreement": read_json(reports / "latest_v688_scenario_disagreement_summary.json"),
        "missed_opportunity": read_json(reports / "latest_v688_missed_opportunity_summary.json"),
        "profit_giveback": read_json(reports / "latest_v688_profit_giveback_summary.json"),
        "variable_convergence": read_json(reports / "latest_v688_variable_convergence_summary.json"),
        "active_analysis": read_json(reports / "latest_v688_active_analysis_recommendations_summary.json"),
        "llm_daily": read_json(reports / "latest_v688_llm_daily_review_summary.json"),
        "llm_weekly": read_json(reports / "latest_v688_llm_weekly_council_summary.json"),
        "llm_monthly": read_json(reports / "latest_v688_llm_monthly_deck_review_summary.json"),
        "tabs": {
            "scenario_telemetry_tab": True,
            "disagreement_tab": True,
            "missed_opportunity_tab": True,
            "profit_giveback_tab": True,
            "variable_convergence_tab": True,
            "active_analysis_tab": True,
            "llm_council_tab": True,
            "route_state_tab": True,
        },
        **safe_status(),
    }
    write_json(reports / "latest_v688_control_tower_dashboard_summary.json", payload)
    build_v688_control_tower_dashboard_report(reports)
    build_astt_report_dashboard(reports)
    return payload


def build_v688_control_tower_dashboard_report(reports_dir: str | Path = "docs/reports") -> str:
    reports = Path(reports_dir)
    payload = read_json(reports / "latest_v688_control_tower_dashboard_summary.json")
    return write_html(
        reports / "latest_v688_control_tower_dashboard_report.html",
        "V6.8.8 Control Tower Dashboard Data",
        [
            ("Scenario Genome", payload.get("scenario_genome", {}).get("cards", [])),
            ("Active Analysis", payload.get("active_analysis", {}).get("recommendations", [])),
            ("LLM Daily", payload.get("llm_daily", {})),
            ("Dashboard Tabs", payload.get("tabs", {})),
        ],
    )


def build_all_reports(reports_dir: str | Path = "docs/reports") -> dict[str, str]:
    reports = Path(reports_dir)
    return {
        "scenario_telemetry": build_scenario_telemetry_report(reports),
        "active_analysis": build_v688_control_tower_dashboard_report(reports),
        "llm_review": build_llm_review_report(reports),
        "astt_dashboard": build_astt_report_dashboard(reports),
    }


def build_astt_report_dashboard(reports_dir: str | Path = "docs/reports") -> str:
    reports = Path(reports_dir)
    links = [
        "latest_v688_scenario_genome_report.html",
        "latest_v688_scenario_telemetry_report.html",
        "latest_v688_scenario_disagreement_report.html",
        "latest_v688_missed_opportunity_report.html",
        "latest_v688_profit_giveback_report.html",
        "latest_v688_variable_convergence_report.html",
        "latest_v688_active_analysis_recommendations_report.html",
        "latest_v688_llm_review_report.html",
        "latest_v688_control_tower_dashboard_report.html",
    ]
    rows = [{"report": name, "exists": (reports / name).exists(), "path": name} for name in links]
    return write_html(reports / "astt_report_dashboard.html", "ASTT Report Dashboard", [("V6.8.8 Reports", rows)])
