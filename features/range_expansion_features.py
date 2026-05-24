from __future__ import annotations


def compute_range_expansion(snapshot: dict) -> dict:
    return {"range_expanding": float(snapshot.get("price_change_30s_pct", 0.0)) > float(snapshot.get("price_change_10s_pct", 0.0)) >= 0, "range_position_pct": float(snapshot.get("range_position_pct", 0.0))}
