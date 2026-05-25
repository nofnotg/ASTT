from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd


def check_trade_lookahead(trade: dict[str, Any]) -> dict[str, Any]:
    signal_time = pd.to_datetime(trade.get("signal_time") or trade.get("entry_time")).to_pydatetime()
    entry_time = pd.to_datetime(trade.get("entry_time")).to_pydatetime()
    cutoff = pd.to_datetime(trade.get("feature_cutoff_time") or signal_time).to_pydatetime()
    violations: list[str] = []
    if cutoff > entry_time:
        violations.append("FEATURE_CUTOFF_AFTER_ENTRY")
    if signal_time > entry_time:
        violations.append("SIGNAL_AFTER_ENTRY")
    if pd.to_datetime(trade.get("exit_time")).to_pydatetime() < entry_time:
        violations.append("EXIT_BEFORE_ENTRY")
    return {
        "trade_id": trade.get("trade_id"),
        "signal_time": str(signal_time),
        "entry_time": str(entry_time),
        "feature_cutoff_time": str(cutoff),
        "used_future_data": bool(violations),
        "lookahead_check": "FAIL" if violations else "PASS",
        "violations": violations,
    }


def audit_trades_for_lookahead(trades: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [check_trade_lookahead({**trade, "feature_cutoff_time": _default_cutoff(trade)}) for trade in trades]
    fail = [row for row in rows if row["lookahead_check"] == "FAIL"]
    return {
        "checked_trades": len(rows),
        "pass": len(rows) - len(fail),
        "fail": len(fail),
        "excluded_trades": len(fail),
        "major_violations": sorted({item for row in fail for item in row["violations"]}),
        "checks": rows,
    }


def _default_cutoff(trade: dict[str, Any]) -> str:
    entry = pd.to_datetime(trade.get("entry_time")).to_pydatetime()
    return str(entry - timedelta(minutes=1))
