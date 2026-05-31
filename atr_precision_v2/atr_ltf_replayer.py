from __future__ import annotations

from typing import Any

from atr_precision_v2.atr_fill_cost_model import apply_fill_costs
from atr_precision_v2.atr_path_schema import ATRReplayConfig
from atr_precision_v2.atr_stop_target_order_resolver import resolve_stop_target_order
from atr_precision_v2.atr_trailing_stop_engine import trailing_stop_hit, update_trailing_stop


def replay_trade_with_ltf(trade: dict[str, Any], bars: list[dict[str, Any]], config: ATRReplayConfig = ATRReplayConfig()) -> dict[str, Any]:
    if not bars:
        return {
            "trade_id": trade.get("trade_id"),
            "market": trade.get("market"),
            "ltf_available": False,
            "bar_count": 0,
            "decision": "ATR_DATA_INSUFFICIENT",
        }
    entry = float(trade.get("entry_price", 0.0) or bars[0].get("open", 0.0) or 0.0)
    position = abs(float(trade.get("position_krw", 0.0) or 0.0))
    atr_value = _atr_proxy(bars, entry)
    stop = float(trade.get("stop_price", 0.0) or entry - atr_value * config.atr_multiplier)
    target = float(trade.get("target_price", 0.0) or entry + atr_value * config.atr_multiplier)
    trailing = stop
    conflict = False
    exit_reason = "TIME_EXIT"
    exit_price = float(bars[-1].get("close", entry))
    exit_time = bars[-1].get("timestamp")
    for bar in bars:
        resolved = resolve_stop_target_order(bar, trailing, target, config.fill_model)
        conflict = conflict or bool(resolved["same_bar_conflict"])
        if resolved["exit_reason"]:
            exit_reason = str(resolved["exit_reason"])
            exit_price = float(resolved["exit_price"])
            exit_time = bar.get("timestamp")
            break
        next_trailing = update_trailing_stop(trailing, bar, atr_value, config.atr_multiplier, config.trailing_update_mode)
        if trailing_stop_hit(bar, trailing):
            exit_reason = "TRAILING_STOP_HIT"
            exit_price = trailing
            exit_time = bar.get("timestamp")
            break
        trailing = next_trailing
    gross = (exit_price / entry - 1.0) * position if entry and position else float(trade.get("pnl_krw", 0.0))
    costs = apply_fill_costs(gross, position, config.fee_pct, config.slippage_pct)
    return {
        "trade_id": trade.get("trade_id"),
        "market": trade.get("market"),
        "ltf_available": True,
        "bar_count": len(bars),
        "entry_price": entry,
        "exit_price": exit_price,
        "exit_time": exit_time,
        "exit_reason": exit_reason,
        "same_bar_conflict": conflict,
        "trailing_stop_final": trailing,
        **costs,
        "decision": "ATR_LTF_REPLAY_READY",
    }


def _atr_proxy(bars: list[dict[str, Any]], fallback_price: float) -> float:
    ranges = [abs(float(row.get("high", 0.0) or 0.0) - float(row.get("low", 0.0) or 0.0)) for row in bars if row.get("high") and row.get("low")]
    if ranges:
        return max(sum(ranges) / len(ranges), fallback_price * 0.002)
    return fallback_price * 0.01
