from __future__ import annotations

from collections import defaultdict


def analyze_plan_performance(journal: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in journal:
        grouped[row["plan"]].append(row)
    rows = []
    for plan, trades in sorted(grouped.items()):
        wins = [row for row in trades if row["pnl_krw"] > 0]
        losses = [row for row in trades if row["pnl_krw"] <= 0]
        gross_win = sum(row["pnl_krw"] for row in wins)
        gross_loss = abs(sum(row["pnl_krw"] for row in losses))
        rows.append({
            "plan": plan,
            "trades": len(trades),
            "pnl_krw": sum(row["pnl_krw"] for row in trades),
            "return_pct": (trades[-1]["equity_after"] - trades[0]["equity_before"]) / trades[0]["equity_before"] * 100 if trades else 0.0,
            "profit_factor": gross_win / gross_loss if gross_loss else (999.0 if wins else 0.0),
            "mdd_pct": min((row.get("drawdown_pct", 0.0) for row in trades), default=0.0),
            "decision": "KEEP_FOR_FORWARD" if gross_win > gross_loss else "PAUSE_OR_DISABLE",
        })
    return rows
