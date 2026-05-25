from __future__ import annotations

from collections import defaultdict


def analyze_strategy_contribution(journal: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    total = sum(row["pnl_krw"] for row in journal)
    for row in journal:
        grouped[row["strategy"]].append(row)
    rows = []
    for strategy, items in sorted(grouped.items()):
        pnl = sum(row["pnl_krw"] for row in items)
        rows.append({
            "strategy": strategy,
            "trades": len(items),
            "pnl_krw": pnl,
            "contribution_pct": pnl / total * 100 if total else 0.0,
            "decision": "KEEP_FOR_FORWARD" if pnl > 0 else "PAUSE",
        })
    return rows
