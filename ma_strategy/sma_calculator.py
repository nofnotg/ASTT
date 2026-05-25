from __future__ import annotations

from collections.abc import Sequence


def simple_moving_average(values: Sequence[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    window = [float(value) for value in values[-period:]]
    return sum(window) / period


def rolling_sma(values: Sequence[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    running = 0.0
    for index, value in enumerate(values):
        running += float(value)
        if index >= period:
            running -= float(values[index - period])
        result.append(running / period if index + 1 >= period else None)
    return result
