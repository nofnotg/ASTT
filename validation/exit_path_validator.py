from __future__ import annotations

from typing import Any


def validate_exit_paths(trades: list[dict[str, Any]]) -> dict[str, Any]:
    invalid = [trade["trade_id"] for trade in trades if not trade.get("exit_time") or not trade.get("exit_price")]
    return {"checked_trades": len(trades), "invalid_exit_count": len(invalid), "invalid_trade_ids": invalid}
