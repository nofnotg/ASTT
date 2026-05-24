from __future__ import annotations


def estimate_liquidity_from_trace(trace_row: dict, price: float, order_krw: float = 500000) -> dict:
    spread_pct = _best_spread(trace_row)
    ratio = _best_ratio(trace_row)
    # Trace artifacts contain top-book ratios, not exact KRW depth. This conservative
    # proxy treats narrow spread plus non-zero book ratio as enough depth for research.
    depth_3_level_krw = order_krw * 3 if spread_pct <= 0.20 and ratio > 0 else order_krw * 0.5
    depth_5_level_krw = depth_3_level_krw * 1.5
    return {
        "estimated_order_krw": order_krw,
        "spread_pct": spread_pct,
        "top_ask_depth_krw": depth_3_level_krw / 2,
        "top_bid_depth_krw": depth_3_level_krw / 2,
        "depth_3_level_krw": depth_3_level_krw,
        "depth_5_level_krw": depth_5_level_krw,
        "depth_sufficiency_ratio": depth_3_level_krw / max(1.0, order_krw),
        "tradable_with_500k": depth_3_level_krw >= order_krw * 2 and spread_pct <= 0.20,
    }


def _best_spread(trace_row: dict) -> float:
    values = [float(row.get("spread_pct", 999.0)) for row in trace_row.get("trace_windows", {}).values()]
    values = [v for v in values if v < 999.0]
    return min(values) if values else 999.0


def _best_ratio(trace_row: dict) -> float:
    values = [float(row.get("bid_ask_size_ratio", 0.0)) for row in trace_row.get("trace_windows", {}).values()]
    return max(values) if values else 0.0
