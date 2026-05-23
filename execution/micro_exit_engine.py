from __future__ import annotations


def decide_micro_exit(entry_context: dict, post_entry_micro: dict, second_candle, orderbook_state=None, elapsed_seconds: int = 0) -> dict:
    entry = float(entry_context.get("entry_price", 0.0))
    target = float(entry_context.get("target_price", entry * 1.006))
    stop = float(entry_context.get("stop_price", entry * 0.994))
    price = float((second_candle or {}).get("close", entry))
    if orderbook_state and orderbook_state.get("liquidity_state") == "WIDE_SPREAD":
        return {"exit_decision": "EMERGENCY_EXIT", "exit_price": price, "reason": ["spread_expanded"], "warnings": []}
    if price >= target:
        return {"exit_decision": "TAKE_PROFIT", "exit_price": target, "reason": ["target_reached"], "warnings": []}
    if price <= stop:
        return {"exit_decision": "STOP_LOSS", "exit_price": stop, "reason": ["hard_stop"], "warnings": []}
    if post_entry_micro.get("micro_failure", False):
        return {"exit_decision": "MICRO_FAILURE_EXIT", "exit_price": price, "reason": ["micro_failure"], "warnings": []}
    if elapsed_seconds >= int(entry_context.get("max_hold_seconds", 120)):
        return {"exit_decision": "TIME_STOP", "exit_price": price, "reason": ["max_hold_seconds"], "warnings": []}
    return {"exit_decision": "HOLD", "exit_price": price, "reason": ["position_ok"], "warnings": []}
