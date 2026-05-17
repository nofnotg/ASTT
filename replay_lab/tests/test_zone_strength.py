from features.zone_strength import compute_zone_strength


def test_zone_strength_penalties():
    strong = compute_zone_strength({"duration_bars": 20, "body_overlap_score": 20, "volume_score": 20, "touch_score": 15, "reaction_score": 15, "recency_score": 10, "zone_width_pct": 1})
    wide = compute_zone_strength({"duration_bars": 20, "body_overlap_score": 20, "volume_score": 20, "touch_score": 15, "reaction_score": 15, "recency_score": 10, "zone_width_pct": 6})
    assert strong["strength"] > wide["strength"]
