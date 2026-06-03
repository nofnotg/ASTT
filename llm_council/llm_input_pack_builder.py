from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from llm_council.llm_token_budget import token_budget
from scenario_telemetry.v688_common import ACTIVE_ROUTE, SHADOW_ROUTES, read_json, write_json


def build_input_pack(review_type: str, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    reports = Path(reports_dir)
    active = read_json(reports / "latest_v688_active_analysis_recommendations_summary.json")
    daily = read_json(reports / "latest_v688_scenario_daily_summary.json")
    weekly = read_json(reports / "latest_v688_scenario_weekly_summary.json")
    monthly = read_json(reports / "latest_v688_scenario_monthly_summary.json")
    disagreement = read_json(reports / "latest_v688_scenario_disagreement_summary.json")
    missed = read_json(reports / "latest_v688_missed_opportunity_summary.json")
    giveback = read_json(reports / "latest_v688_profit_giveback_summary.json")
    convergence = read_json(reports / "latest_v688_variable_convergence_summary.json")
    today = date.today().isoformat()
    pack = {
        "input_pack_id": f"v688_{review_type}_{today}",
        "review_type": review_type,
        "period": today,
        "raw_log_included": False,
        "token_budget": token_budget(review_type),
        "active_route": ACTIVE_ROUTE,
        "shadow_routes": SHADOW_ROUTES,
        "market_state_summary": {"source": "scenario_telemetry", "status": "summary_only"},
        "candidates_count": active.get("pipeline_health", {}).get("candidate_count", 0),
        "entries_count": active.get("no_trade_reason", {}).get("enter_count", 0),
        "wait_count": active.get("pipeline_health", {}).get("candidate_count", 0),
        "top_skip_reasons": active.get("no_trade_reason", {}).get("top_reasons", []),
        "trades_summary": {"source": "paper summary only"},
        "pnl_summary": {"daily_rows": len(daily.get("rows", []))},
        "active_vs_shadow_delta": active.get("active_shadow_delta", {}),
        "missed_opportunity_summary": {k: missed.get(k) for k in ("missed_opportunity_count", "top_false_block_reasons", "decision")},
        "giveback_flags": {"candidate_count": len(giveback.get("profit_lock_candidate", []))},
        "pipeline_health": active.get("pipeline_health", {}),
        "active_analysis_recommendations": active.get("recommendations", []),
        "week": (weekly.get("rows", [{}])[-1] if weekly.get("rows") else {}).get("week"),
        "month": (monthly.get("rows", [{}])[-1] if monthly.get("rows") else {}).get("month"),
        "market_state_distribution": (weekly.get("rows", [{}])[-1] if weekly.get("rows") else {}).get("market_state_distribution", {}),
        "scenario_weekly_stats": weekly.get("rows", [])[-10:],
        "scenario_deck_status": read_json(reports / "latest_v688_scenario_genome_summary.json").get("cards", []),
        "monthly_scenario_stats": monthly.get("rows", [])[-10:],
        "market_state_performance": {},
        "variable_convergence": convergence,
        "variable_convergence_summary": convergence,
        "disagreement_summary": {k: disagreement.get(k) for k in ("type_counts", "row_count")},
        "profit_giveback_summary": {k: giveback.get(k) for k in ("row_count", "decision")},
        "failure_signatures": [],
        "promotion_candidates": [],
        "demotion_candidates": [],
        "proposed_new_tests": [],
        "token_budget_used": token_budget(review_type),
    }
    write_json(reports / f"latest_v688_llm_{review_type}_input_pack_summary.json", pack)
    return pack
