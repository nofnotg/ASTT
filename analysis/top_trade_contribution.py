from __future__ import annotations


def top_win_contribution(trades: list[dict], top_n: int) -> float:
    wins = sorted([row["pnl_krw"] for row in trades if row.get("pnl_krw", 0) > 0], reverse=True)
    total = sum(row.get("pnl_krw", 0) for row in trades)
    if total <= 0 or not wins:
        return 0.0
    return sum(wins[:top_n]) / total * 100
