from __future__ import annotations


REQUIRED_FIELDS = {
    "daily": ["date", "market_state_summary", "active_route", "shadow_routes", "candidates_count", "entries_count", "wait_count", "top_skip_reasons", "pipeline_health", "active_analysis_recommendations"],
    "weekly": ["week", "market_state_distribution", "scenario_weekly_stats", "disagreement_summary", "missed_opportunity_summary", "profit_giveback_summary", "variable_convergence_summary", "active_analysis_recommendations"],
    "monthly": ["month", "scenario_deck_status", "monthly_scenario_stats", "market_state_performance", "variable_convergence", "failure_signatures", "promotion_candidates", "demotion_candidates", "token_budget_used"],
}
