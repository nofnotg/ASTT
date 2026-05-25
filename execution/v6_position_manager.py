from __future__ import annotations


def summarize_v6_trades(trades: list[dict], initial_cash_krw: float = 500000) -> dict:
    wins = [row for row in trades if row["pnl_krw"] > 0]
    losses = [row for row in trades if row["pnl_krw"] <= 0]
    gross_win = sum(row["pnl_krw"] for row in wins)
    gross_loss = abs(sum(row["pnl_krw"] for row in losses))
    total = sum(row["pnl_krw"] for row in trades)
    return {
        "trade_count": len(trades),
        "win_rate": len(wins) / len(trades) if trades else 0.0,
        "average_win_pct": sum(row["return_pct"] for row in wins) / len(wins) if wins else 0.0,
        "average_loss_pct": sum(row["return_pct"] for row in losses) / len(losses) if losses else 0.0,
        "profit_factor": gross_win / gross_loss if gross_loss else (None if not wins else 999.0),
        "expectancy_pct": sum(row["return_pct"] for row in trades) / len(trades) if trades else 0.0,
        "total_pnl_krw": total,
        "total_return_pct": total / initial_cash_krw * 100 if initial_cash_krw else 0.0,
    }
