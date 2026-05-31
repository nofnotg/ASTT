from __future__ import annotations

from typing import Any


def resolve_stop_target_order(bar: dict[str, Any], stop_price: float, target_price: float, fill_model: str = "conservative") -> dict[str, Any]:
    high = float(bar.get("high", 0.0) or 0.0)
    low = float(bar.get("low", 0.0) or 0.0)
    open_price = float(bar.get("open", 0.0) or 0.0)
    stop_hit = stop_price > 0.0 and low <= stop_price
    target_hit = target_price > 0.0 and high >= target_price
    if stop_hit and target_hit:
        if fill_model == "optimistic":
            return {"exit_reason": "TARGET_SAME_BAR_OPTIMISTIC", "exit_price": target_price, "same_bar_conflict": True}
        if fill_model == "neutral":
            first = "STOP" if abs(open_price - stop_price) <= abs(open_price - target_price) else "TARGET"
            price = stop_price if first == "STOP" else target_price
            return {"exit_reason": f"{first}_SAME_BAR_NEUTRAL", "exit_price": price, "same_bar_conflict": True}
        return {"exit_reason": "STOP_SAME_BAR_CONSERVATIVE", "exit_price": stop_price, "same_bar_conflict": True}
    if stop_hit:
        return {"exit_reason": "STOP_HIT", "exit_price": stop_price, "same_bar_conflict": False}
    if target_hit:
        return {"exit_reason": "TARGET_HIT", "exit_price": target_price, "same_bar_conflict": False}
    return {"exit_reason": None, "exit_price": None, "same_bar_conflict": False}
