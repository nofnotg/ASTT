from __future__ import annotations


def select_weekly_strategy(results: dict) -> str:
    strategies = results.get("strategies", {})
    if not strategies:
        return "NONE"
    return max(strategies, key=lambda name: strategies[name].get("expectancy_pct", -999))
