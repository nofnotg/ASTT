from __future__ import annotations

from typing import Any


def sensitivity_factor(period: int, multiplier: float, timeframe: str, model: str) -> float:
    period_penalty = 1.0 - abs(period - 14) * 0.01
    multiplier_penalty = 1.0 - abs(multiplier - 2.0) * 0.08
    timeframe_penalty = {"5m": 0.92, "15m": 0.96, "1h": 1.0}.get(timeframe, 0.9)
    model_penalty = {"conservative": 0.70, "neutral": 0.85, "optimistic": 0.95}.get(model, 0.75)
    return max(0.15, period_penalty * multiplier_penalty * timeframe_penalty * model_penalty)
