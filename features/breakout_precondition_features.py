from __future__ import annotations


def compute_breakout_preconditions(snapshot: dict) -> dict:
    near_high = float(snapshot.get("previous_high_distance_pct", 999)) <= 0.25
    range_high = float(snapshot.get("range_position_pct", 0)) >= 70
    return {"near_previous_high": near_high, "range_high_position": range_high, "breakout_precondition_score": (50 if near_high else 0) + (50 if range_high else 0)}
