from __future__ import annotations


def compute_tradable_depth(snapshot: dict, order_krw: float = 500000) -> dict:
    spread_pct = float(snapshot.get("spread_pct", 999.0))
    ratio = float(snapshot.get("bid_ask_size_ratio", 0.0))
    depth_3_level_krw = order_krw * 3 if spread_pct <= 0.20 and ratio > 0 else order_krw * 0.5
    return {
        "depth_3_level_krw": depth_3_level_krw,
        "depth_sufficiency_ratio": depth_3_level_krw / max(1.0, order_krw),
        "tradable_with_500k": depth_3_level_krw >= order_krw * 2,
    }
