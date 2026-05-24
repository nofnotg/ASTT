from __future__ import annotations

from tradable_winner.tradable_depth_model import is_tradable_depth
from tradable_winner.tradable_effective_return import calculate_tradable_effective_return
from tradable_winner.tradable_spread_model import calculate_spread_pct
from tradable_winner.tradable_winner_schema import WINNER_TYPE_CONFIG
from winner_mining.tick_noise_filter import evaluate_tick_noise


def apply_tradable_winner_prefilter(
    market: str,
    start_price: float,
    peak_price: float,
    orderbook: dict,
    winner_type: str,
    trade_event_count: int = 0,
    orderbook_event_count: int = 0,
    fee_pct: float = 0.05,
) -> dict:
    config = WINNER_TYPE_CONFIG[winner_type]
    raw_return_pct = ((peak_price - start_price) / start_price) * 100 if start_price > 0 else 0.0
    units = orderbook.get("units") or orderbook.get("orderbook_units") or []
    top = units[0] if units else {}
    spread_pct = calculate_spread_pct(float(top.get("bid_price", 0.0) or 0.0), float(top.get("ask_price", 0.0) or 0.0))
    depth_3 = is_tradable_depth(orderbook, config["depth_3_required_krw"], levels=3)
    depth_5 = is_tradable_depth(orderbook, config["depth_5_required_krw"], levels=5)
    effective = calculate_tradable_effective_return(
        raw_return_pct,
        entry_spread_cost_pct=spread_pct / 2,
        exit_spread_cost_pct=spread_pct / 2,
        slippage_pct=config["slippage_pct"],
        fee_pct=fee_pct,
    )
    tick = evaluate_tick_noise(start_price, peak_price, effective["effective_return_pct"])
    reject_reasons: list[str] = []
    if not market.startswith("KRW-"):
        reject_reasons.append("NOT_KRW_MARKET")
    if spread_pct > config["max_spread_pct"]:
        reject_reasons.append("SPREAD_TOO_WIDE")
    if not depth_3["tradable"] or not depth_5["tradable"]:
        reject_reasons.append("DEPTH_INSUFFICIENT")
    if effective["effective_return_pct"] < config["min_effective_return_pct"]:
        reject_reasons.append("EFFECTIVE_RETURN_TOO_LOW")
    if effective["reward_to_cost_ratio"] < config["min_reward_to_cost"]:
        reject_reasons.append("REWARD_TO_COST_TOO_LOW")
    if tick["is_tick_noise"]:
        reject_reasons.append("TICK_NOISE")
    if trade_event_count <= 0 or orderbook_event_count <= 0:
        reject_reasons.append("DATA_QUALITY_POOR")
    return {
        "prefilter_pass": not reject_reasons,
        "raw_return_pct": raw_return_pct,
        "spread_pct": spread_pct,
        "depth_3_level_krw": depth_3["depth_krw"],
        "depth_5_level_krw": depth_5["depth_krw"],
        "tradable_with_500k": depth_3["tradable"] and depth_5["tradable"],
        "tick_noise": tick["is_tick_noise"],
        "reject_reasons": reject_reasons,
        **effective,
    }
