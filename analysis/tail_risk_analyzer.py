from __future__ import annotations


def max_losing_streak(trades: list[dict]) -> int:
    best = run = 0
    for trade in trades:
        if trade.get("pnl_krw", 0) <= 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best
