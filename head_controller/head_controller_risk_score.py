from __future__ import annotations


def compute_head_controller_risk_score(summary: dict) -> dict:
    score = 0
    if summary.get("artifact_integrity_status") == "PASS":
        score += 20
    if summary.get("enter_count", 0) >= 30:
        score += 15
    if summary.get("profit_factor") and summary.get("profit_factor") >= 1.1:
        score += 20
    if summary.get("expectancy_pct") and summary.get("expectancy_pct") > 0:
        score += 20
    if summary.get("max_drawdown_pct", 0) >= -5:
        score += 15
    if summary.get("reproducible"):
        score += 10
    return {"research_score": score, "risk_level": "HIGH" if score < 40 else "MEDIUM" if score < 70 else "LOW"}
