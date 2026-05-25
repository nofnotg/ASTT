from __future__ import annotations


def build_equity_curve(journal: list[dict]) -> list[dict]:
    return [{"time": row["exit_time"], "equity": row["equity_after"], "drawdown_pct": row["drawdown_pct"]} for row in journal]
