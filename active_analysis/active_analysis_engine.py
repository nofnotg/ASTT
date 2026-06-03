from __future__ import annotations

from pathlib import Path
from typing import Any

from active_analysis.active_analysis_report_builder import build_active_analysis_report
from active_analysis.active_shadow_delta_analyzer import analyze_active_shadow_delta
from active_analysis.candidate_to_ledger_analyzer import analyze_candidate_to_ledger
from active_analysis.forward_pipeline_health_analyzer import analyze_forward_pipeline
from active_analysis.no_trade_reason_analyzer import analyze_no_trade_reasons
from active_analysis.proactive_experiment_generator import experiments_from_triggers
from active_analysis.route_health_analyzer import route_state
from scenario_telemetry.v688_common import load_context, read_json, safe_status, write_json


def run_active_analysis_engine(reports_dir: str | Path = "docs/reports", data_dir: str | Path = "data/paper") -> dict[str, Any]:
    ctx = load_context(reports_dir, data_dir)
    reports = Path(reports_dir)
    genome = read_json(reports / "latest_v688_scenario_genome_summary.json")
    pipeline = analyze_forward_pipeline(ctx["forward_summary"], ctx["forward_events"])
    ledger = analyze_candidate_to_ledger(ctx["forward_events"], ctx["trades"])
    route = route_state(ctx["backfill"], ctx["runtime"], genome)
    no_trade = analyze_no_trade_reasons(ctx["forward_events"])
    delta = analyze_active_shadow_delta(ctx["backfill"])
    recommendations = experiments_from_triggers(pipeline, no_trade, delta, route)
    payload = {
        "schema_version": "v688_active_analysis_v1",
        "pipeline_health": pipeline,
        "candidate_to_ledger": ledger,
        "route_state": route,
        "no_trade_reason": no_trade,
        "active_shadow_delta": delta,
        "recommendations": recommendations,
        "recommendation_count": len(recommendations),
        **safe_status(),
    }
    write_json(reports / "latest_v688_active_analysis_recommendations_summary.json", payload)
    build_active_analysis_report(payload, reports)
    return payload
