from __future__ import annotations


def decide_strategy(summary: dict, dependency: dict | None = None, split: dict | None = None) -> str:
    trades = int(summary.get("trade_count", 0))
    expectancy = float(summary.get("expectancy_pct", 0.0))
    mdd = float(summary.get("max_drawdown_pct", 0.0))
    dep = (dependency or {}).get("dependency_decision")
    split_decision = (split or {}).get("decision")
    if trades == 0:
        return "DATA_OR_DETECTOR_FAILURE"
    if expectancy > 0 and mdd > -8 and dep != "RANDOM_SPIKE_SUSPECTED" and split_decision != "WEAK":
        return "STRATEGY_KEEP_FOR_FORWARD"
    if expectancy > 0:
        return "STRATEGY_KEEP_WITH_FILTER"
    if expectancy > -1:
        return "STRATEGY_PAUSE"
    return "STRATEGY_DISABLE"
