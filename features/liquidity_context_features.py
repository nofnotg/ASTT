from __future__ import annotations


def liquidity_context_pass(snapshot: dict, min_depth_3_krw: float = 1_000_000, max_spread_pct: float = 0.20) -> bool:
    return float(snapshot.get("depth_3_level_krw", 0.0) or 0.0) >= min_depth_3_krw and float(snapshot.get("spread_pct", 999.0) or 999.0) <= max_spread_pct
