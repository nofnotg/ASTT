from __future__ import annotations

from typing import Any


def update_trailing_stop(current_stop: float, bar: dict[str, Any], atr_value: float, multiplier: float, mode: str) -> float:
    close = float(bar.get("close", 0.0) or 0.0)
    high = float(bar.get("high", 0.0) or 0.0)
    anchor = high if mode == "high_low_intrabar_conservative" else close
    candidate = anchor - atr_value * multiplier
    return max(current_stop, candidate) if current_stop > 0 else candidate


def trailing_stop_hit(bar: dict[str, Any], trailing_stop: float) -> bool:
    return trailing_stop > 0 and float(bar.get("low", 0.0) or 0.0) <= trailing_stop
