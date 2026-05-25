from __future__ import annotations


def slope_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None or previous == 0:
        return None
    return (float(current) / float(previous) - 1.0) * 100.0


def is_up_slope(value: float | None, threshold_pct: float = 0.0) -> bool:
    return value is not None and value > threshold_pct


def is_down_slope(value: float | None, threshold_pct: float = 0.0) -> bool:
    return value is not None and value < -abs(threshold_pct)
