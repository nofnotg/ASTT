from __future__ import annotations


def compute_zone_strength(metrics: dict) -> dict:
    width = float(metrics.get("zone_width_pct", 0.0))
    score = 0.0
    score += min(20.0, float(metrics.get("duration_bars", 0)) / 20 * 20)
    score += min(20.0, float(metrics.get("body_overlap_score", 0.0)))
    score += min(20.0, float(metrics.get("volume_score", 0.0)))
    score += min(15.0, float(metrics.get("touch_score", 0.0)))
    score += min(15.0, float(metrics.get("reaction_score", 0.0)))
    score += min(10.0, float(metrics.get("recency_score", 0.0)))
    if width > 3.0:
        score -= min(30.0, (width - 3.0) * 10)
    if float(metrics.get("volume_score", 0.0)) < 5:
        score -= 20
    if float(metrics.get("wick_ratio", 0.0)) > 0.65:
        score -= 15
    if float(metrics.get("pierce_count", 0.0)) >= 3:
        score -= 20
    if float(metrics.get("target_space_pct", 999.0)) < 0.8:
        score -= 20
    return {"strength": max(0.0, min(100.0, score))}
