from __future__ import annotations


def manage_open_position(position: dict, snapshot: dict, config: dict | None = None) -> dict:
    cfg = {"max_hold_seconds": 120, "micro_failure_watch_seconds": 10, **(config or {})}
    price = float(snapshot.get("last_price", 0.0))
    elapsed = (int(snapshot.get("timestamp_ms", 0)) - int(position.get("entry_time_ms", 0))) / 1000
    if price >= float(position.get("target_price", 10**18)):
        return {"decision": "TAKE_PROFIT", "reason": ["target_price_hit"], "snapshot_time_ms": snapshot.get("timestamp_ms")}
    if price <= float(position.get("stop_price", -1)):
        return {"decision": "STOP_LOSS", "reason": ["stop_price_hit"], "snapshot_time_ms": snapshot.get("timestamp_ms")}
    if elapsed <= cfg["micro_failure_watch_seconds"] and snapshot.get("price_change_3s_pct", 0.0) < 0 and snapshot.get("buy_trade_ratio_3s", 1.0) < 0.5:
        return {"decision": "MICRO_FAILURE_EXIT", "reason": ["follow_through_failed"], "snapshot_time_ms": snapshot.get("timestamp_ms")}
    if elapsed >= cfg["max_hold_seconds"]:
        return {"decision": "TIME_STOP", "reason": ["max_hold_seconds"], "snapshot_time_ms": snapshot.get("timestamp_ms")}
    return {"decision": "HOLD", "reason": [], "snapshot_time_ms": snapshot.get("timestamp_ms")}
