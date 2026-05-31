from __future__ import annotations

from typing import Any


def chandelier_stop(bars: list[dict[str, Any]], atr_value: float, multiplier: float) -> float:
    if not bars:
        return 0.0
    highest = max(float(row.get("high", 0.0) or 0.0) for row in bars)
    return highest - atr_value * multiplier
