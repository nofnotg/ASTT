from __future__ import annotations


def compute_fractal_mtf_context(weekly_result, daily_result, h4_result, h1_result, m15_result, m5_result, m1_result=None) -> dict:
    weekly_score = float(weekly_result.get("weekly_power_score", weekly_result.get("weekly_bias_score", 0.0)))
    daily_score = float(daily_result.get("daily_structure_score", 0.0))
    h4_score = float(h4_result.get("h4_flow_score", 0.0))
    lower_score = max(float(h1_result.get("score", 0.0)), float(m15_result.get("score", 0.0)), float(m5_result.get("score", 0.0)), float((m1_result or {}).get("score", 0.0)))
    alignment = weekly_score * 0.30 + daily_score * 0.25 + h4_score * 0.25 + lower_score * 0.20
    conflict = max(0.0, lower_score - min(weekly_score, daily_score, h4_score))
    if weekly_score >= 65 and daily_score >= 60 and h4_score >= 55:
        state = "FULL_ALIGNMENT"
        mode = "FULL_SEED"
        bias = "BULL"
    elif daily_score >= 60 and h4_score >= 55:
        state = "HIGHER_TIMEFRAME_SUPPORT"
        mode = "PARTIAL_SEED"
        bias = "NEUTRAL"
    elif lower_score >= 70 and min(weekly_score, daily_score, h4_score) < 45:
        state = "LOWER_TIMEFRAME_ONLY"
        mode = "PAPER_ONLY"
        bias = "BEAR" if weekly_score < 40 else "NEUTRAL"
    elif min(weekly_score, daily_score, h4_score) < 35:
        state = "RISK"
        mode = "NO_TRADE"
        bias = "BEAR"
    else:
        state = "CONFLICT"
        mode = "PAPER_ONLY"
        bias = "NEUTRAL"
    trigger = "READY" if lower_score >= 70 else "EARLY" if lower_score >= 50 else "NONE"
    return {
        "fractal_alignment_score": max(0.0, min(100.0, alignment)),
        "fractal_state": state,
        "conflict_level": conflict,
        "higher_timeframe_bias": bias,
        "lower_timeframe_trigger": trigger,
        "recommended_mode": mode,
        "reasons": [state.lower()],
        "warnings": ["fractal_conflict"] if state in {"CONFLICT", "LOWER_TIMEFRAME_ONLY"} else [],
    }
