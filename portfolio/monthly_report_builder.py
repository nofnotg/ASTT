from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd


def build_monthly_rows(journal: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in journal:
        month = str(pd.to_datetime(row["date"]).to_period("M"))
        groups[month].append(row)
    rows = []
    for month, items in sorted(groups.items()):
        start = items[0]["equity_before"]
        end = items[-1]["equity_after"]
        wins = [row for row in items if row["pnl_krw"] > 0]
        losses = [row for row in items if row["pnl_krw"] <= 0]
        gross_win = sum(row["pnl_krw"] for row in wins)
        gross_loss = abs(sum(row["pnl_krw"] for row in losses))
        rows.append({
            "month": month,
            "start_equity": start,
            "end_equity": end,
            "return_pct": (end - start) / start * 100 if start else 0.0,
            "trades": len(items),
            "win_rate": len(wins) / len(items) if items else 0.0,
            "profit_factor": gross_win / gross_loss if gross_loss else (999.0 if wins else 0.0),
            "mdd_pct": min(row["drawdown_pct"] for row in items),
            "top_strategy": Counter(row["strategy"] for row in items).most_common(1)[0][0],
            "risk_note": "큰 승리 의존과 OHLCV-only 체결 착시를 계속 감시해야 합니다.",
        })
    return rows
