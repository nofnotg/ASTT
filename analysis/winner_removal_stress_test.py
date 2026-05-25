from __future__ import annotations

from execution.v6_position_manager import summarize_v6_trades


def remove_top_winners(trades: list[dict], top_n: int, initial_cash_krw: float = 500000) -> dict:
    winners = sorted([row for row in trades if row.get("pnl_krw", 0) > 0], key=lambda row: row["pnl_krw"], reverse=True)
    remove_ids = {row["trade_id"] for row in winners[:top_n]}
    remaining = [row for row in trades if row["trade_id"] not in remove_ids]
    return summarize_v6_trades(remaining, initial_cash_krw)
