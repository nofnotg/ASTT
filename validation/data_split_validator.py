from __future__ import annotations

from typing import Any

import pandas as pd

from execution.v6_position_manager import summarize_v6_trades


def split_trades_train_validation_test(trades: list[dict[str, Any]], initial_cash_krw: float = 500000) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda row: pd.to_datetime(row["entry_time"]))
    n = len(ordered)
    train_end = int(n * 0.6)
    validation_end = int(n * 0.8)
    splits = {
        "train": ordered[:train_end],
        "validation": ordered[train_end:validation_end],
        "test": ordered[validation_end:],
    }
    summary = {name: summarize_v6_trades(rows, initial_cash_krw) for name, rows in splits.items()}
    decision = "PASS" if summary["validation"]["total_return_pct"] >= 0 and summary["test"]["total_return_pct"] > -5 else "WEAK"
    return {"split_counts": {name: len(rows) for name, rows in splits.items()}, "summary": summary, "decision": decision}
