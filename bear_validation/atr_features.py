from __future__ import annotations

from typing import Any


def atr_stop_distance_proxy(row: dict[str, Any], multiplier: float = 2.0) -> float:
    entry = float(row.get("entry_price", 0.0) or 0.0)
    stop = float(row.get("stop_price", 0.0) or 0.0)
    distance = abs(entry - stop)
    return distance * multiplier
