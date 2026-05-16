from __future__ import annotations


def compute_v5_score(inputs: dict) -> dict:
    weekly = float(inputs.get("weekly_bias_score", 0.0))
    daily = float(inputs.get("daily_structure_score", 0.0))
    h4 = float(inputs.get("h4_flow_score", 0.0))
    structure = float(inputs.get("structure_quality_score", 0.0))
    setup = float(inputs.get("setup_score", 0.0))
    trigger = float(inputs.get("trigger_score", 0.0))
    risk_reward_score = min(100.0, float(inputs.get("risk_reward", 0.0)) / 1.8 * 100)
    v5_score = weekly * 0.15 + daily * 0.20 + h4 * 0.20 + structure * 0.15 + setup * 0.10 + trigger * 0.10 + risk_reward_score * 0.10
    entry_allowed = bool(v5_score >= 75 and weekly >= 50 and daily >= 60 and h4 >= 55 and float(inputs.get("risk_reward", 0.0)) >= 1.2)
    grade = "A" if v5_score >= 85 and entry_allowed else "B" if v5_score >= 75 and entry_allowed else "C" if v5_score >= 65 else "REJECT"
    warnings = []
    if weekly < 50:
        warnings.append("weekly_bias_weak")
    if daily < 60:
        warnings.append("daily_structure_weak")
    if h4 < 55:
        warnings.append("h4_flow_weak")
    if float(inputs.get("risk_reward", 0.0)) < 1.2:
        warnings.append("risk_reward_low")
    return {
        "v5_score": float(max(0.0, min(100.0, v5_score))),
        "grade": grade,
        "entry_allowed": entry_allowed,
        "top_reasons": inputs.get("reasons", [])[:5],
        "warnings": warnings,
        "component_scores": {
            "weekly_bias": weekly,
            "daily_structure": daily,
            "h4_flow": h4,
            "structure_quality": structure,
            "setup": setup,
            "trigger": trigger,
            "risk_reward": risk_reward_score,
        },
    }
