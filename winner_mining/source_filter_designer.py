from __future__ import annotations


def design_refined_source_filters(discriminative_power: dict) -> dict:
    top = discriminative_power.get("top_features", [])
    return {
        "ORDERFLOW_SURGE_REFINED": ["buy_trade_ratio_10s", "orderbook_imbalance", "spread_pct"],
        "VOLUME_RANGE_BREAKOUT_REFINED": ["volume_burst_ratio_10s_vs_60s", "previous_high_distance_pct", "spread_pct"],
        "RANGE_COMPRESSION_EXPANSION_REFINED": top or ["previous_high_distance_pct", "volume_burst_ratio_10s_vs_60s", "buy_trade_ratio_10s"],
        "auto_apply_allowed": False,
        "live_order_allowed": False,
    }
