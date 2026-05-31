from __future__ import annotations

from pathlib import Path
from typing import Any

from atr_ltf.ltf_data_finder import find_ltf_files
from atr_ltf.ltf_data_schema import TIMEFRAMES
from atr_ltf.ltf_ohlcv_loader import bars_between, load_ltf_bars


def analyze_ltf_coverage(trades: list[dict[str, Any]], search_roots: list[str | Path] | None = None) -> dict[str, Any]:
    rows = []
    covered = {timeframe: 0 for timeframe in TIMEFRAMES}
    for trade in trades:
        market = str(trade.get("market") or "")
        trade_row = {"trade_id": trade.get("trade_id"), "market": market}
        any_covered = False
        for timeframe in TIMEFRAMES:
            files = find_ltf_files(market, timeframe, search_roots)
            count = 0
            for path in files[:3]:
                count += len(bars_between(load_ltf_bars(path, market, timeframe), str(trade.get("entry_time", "")), str(trade.get("exit_time", ""))))
            is_covered = count > 0
            trade_row[f"covered_by_{timeframe}"] = is_covered
            trade_row[f"{timeframe}_bar_count"] = count
            trade_row[f"{timeframe}_source_count"] = len(files)
            if is_covered:
                covered[timeframe] += 1
                any_covered = True
        trade_row["uncovered"] = not any_covered
        rows.append(trade_row)
    total = len(trades)
    best_pct = max([(covered[timeframe] / total * 100.0 if total else 0.0) for timeframe in TIMEFRAMES] + [0.0])
    decision = "ATR_LTF_READY" if best_pct >= 80.0 else "ATR_DATA_INSUFFICIENT"
    return {
        "total_atr_trades": total,
        "covered_by_1m": covered["1m"],
        "covered_by_5m": covered["5m"],
        "covered_by_15m": covered["15m"],
        "uncovered": sum(1 for row in rows if row["uncovered"]),
        "coverage_pct_1m": covered["1m"] / total * 100.0 if total else 0.0,
        "coverage_pct_5m": covered["5m"] / total * 100.0 if total else 0.0,
        "coverage_pct_15m": covered["15m"] / total * 100.0 if total else 0.0,
        "best_coverage_pct": best_pct,
        "fake_data_generated": False,
        "trade_rows": rows[:300],
        "decision": decision,
    }
