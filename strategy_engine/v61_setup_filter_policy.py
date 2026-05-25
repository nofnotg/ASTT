from __future__ import annotations


def setup_decision(expectancy_pct: float, trade_count: int) -> str:
    if trade_count == 0:
        return "DATA_OR_DETECTOR_FAILURE"
    if expectancy_pct > 0:
        return "KEEP"
    if expectancy_pct > -1:
        return "PAUSE"
    return "DISABLE"
