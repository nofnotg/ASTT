from __future__ import annotations


def classify_structure_reversal(inputs: dict) -> dict:
    weekly = inputs.get("weekly", {})
    daily = inputs.get("daily", {})
    h4 = inputs.get("h4", {})
    rs_flip = inputs.get("rs_flip", {})
    trendline = inputs.get("trendline", {})
    body = inputs.get("body_zone", {})
    if weekly.get("weekly_bias_score", 0) >= 60 and daily.get("support_held") and h4.get("ma_reclaimed"):
        strategy = "TREND_CONTINUATION_PULLBACK"
    elif rs_flip.get("has_rs_flip") and daily.get("support_held"):
        strategy = "FAILED_BREAKDOWN_RECLAIM"
    elif weekly.get("weekly_state") in {"RECOVERING", "NEUTRAL"} and trendline.get("resistance_trendline_broken"):
        strategy = "BOTTOM_REVERSAL"
    else:
        strategy = "NONE"
    score = max(
        float(rs_flip.get("rs_flip_score", 0.0)),
        float(trendline.get("trendline_score", 0.0)),
        float(body.get("body_zone_score", 0.0)),
    )
    return {
        "strategy_type": strategy,
        "structure_quality_score": score,
        "has_structure_reversal": strategy != "NONE",
        "reasons": [strategy.lower()] if strategy != "NONE" else [],
    }
