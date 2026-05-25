from __future__ import annotations

from collections import defaultdict

from execution.v6_position_manager import summarize_v6_trades


def classify_trade_regime(trade: dict) -> str:
    setup = trade.get("setup_type", "")
    if "LIQUIDITY_SWEEP" in setup:
        return "ALT_ROTATION"
    if "FVG" in setup:
        return "HIGH_VOLATILITY"
    if "NECKLINE" in setup or "SR_FLIP" in setup:
        return "BULL"
    return "CHOP"


def analyze_regime_performance(strategy: str, trades: list[dict], initial_cash_krw: float = 500000) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for trade in trades:
        groups[classify_trade_regime(trade)].append(trade)
    rows = []
    for regime, items in sorted(groups.items()):
        perf = summarize_v6_trades(items, initial_cash_krw)
        rows.append({"strategy": strategy, "regime": regime, **perf, "decision": _decision(perf)})
    return rows


def _decision(perf: dict) -> str:
    if perf["trade_count"] == 0:
        return "DATA_OR_DETECTOR_FAILURE"
    if perf["expectancy_pct"] > 0:
        return "KEEP_WITH_REGIME_FILTER"
    return "AVOID"
