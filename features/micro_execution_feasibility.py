from __future__ import annotations


def assess_micro_execution_feasibility(setup_context: dict, liquidity_context: dict, cost_context: dict) -> dict:
    target_pct = abs(float(setup_context.get("expected_target_pct", 0.6)))
    spread = float(liquidity_context.get("spread_pct", 999.0))
    cost = float(cost_context.get("cost_pct", cost_context.get("estimated_total_cost_pct", 999.0)))
    ratio = cost / target_pct if target_pct else 999.0
    warnings = []
    decision = "TRADEABLE"
    if liquidity_context.get("liquidity_state") in {"NO_DATA", "THIN"}:
        decision = "NO_DATA" if liquidity_context.get("liquidity_state") == "NO_DATA" else "TOO_THIN"
    elif spread > 0.25:
        decision = "TOO_EXPENSIVE"
    elif ratio >= 0.30:
        decision = "TOO_EXPENSIVE"
    feasible = decision == "TRADEABLE"
    if not feasible:
        warnings.append(decision.lower())
    return {"feasible": feasible, "feasibility_score": max(0.0, 100.0 - ratio * 100), "cost_to_target_ratio": ratio, "warnings": warnings, "decision": decision}
