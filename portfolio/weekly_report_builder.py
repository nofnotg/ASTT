from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd


def build_weekly_rows(journal: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in journal:
        week = str(pd.to_datetime(row["date"]).to_period("W").start_time.date())
        groups[week].append(row)
    return [_period_row("week", key, rows) for key, rows in sorted(groups.items())]


def _period_row(label: str, key: str, rows: list[dict]) -> dict:
    start = rows[0]["equity_before"]
    end = rows[-1]["equity_after"]
    wins = [row for row in rows if row["pnl_krw"] > 0]
    losses = [row for row in rows if row["pnl_krw"] <= 0]
    best = max(rows, key=lambda row: row["pnl_krw"])
    worst = min(rows, key=lambda row: row["pnl_krw"])
    strategy = Counter(row["strategy"] for row in rows).most_common(1)[0][0]
    return {
        label: key,
        "start_equity": start,
        "end_equity": end,
        "return_pct": (end - start) / start * 100 if start else 0.0,
        "trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(rows) if rows else 0.0,
        "mdd_pct": min(row["drawdown_pct"] for row in rows),
        "best_trade": best["trade_id"],
        "worst_trade": worst["trade_id"],
        "main_strategy": strategy,
        "interpretation": _interpret(rows, start, end),
    }


def _interpret(rows: list[dict], start: float, end: float) -> str:
    if end >= start:
        return "수익 구간입니다. 큰 승리와 제한된 손실이 계좌를 끌어올렸습니다."
    return "손실 구간입니다. 불리한 setup 또는 작은 손실 반복을 줄여야 합니다."
