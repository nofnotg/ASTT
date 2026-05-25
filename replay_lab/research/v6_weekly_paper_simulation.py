from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def run_v6_weekly_paper_simulation(months: int = 12, initial_cash_krw: float = 500000, paper_entry_policy: str = "ACTIVE_RESEARCH") -> dict[str, Any]:
    summaries = [
        _read(Path("docs/reports/latest_v6_daddy_strategy_summary.json")),
        _read(Path("docs/reports/latest_v6_ict_strategy_summary.json")),
        _read(Path("docs/reports/latest_v6_combined_strategy_summary.json")),
    ]
    trades = []
    for summary in summaries:
        trades.extend(summary.get("trades", []))
    weeks = defaultdict(list)
    for trade in trades:
        key = str(trade.get("exit_time", ""))[:10] or "UNKNOWN"
        weeks[key].append(trade)
    equity = initial_cash_krw
    rows = []
    peak = equity
    for week, week_trades in sorted(weeks.items()):
        pnl = sum(float(row.get("pnl_krw", 0.0)) for row in week_trades)
        equity += pnl
        peak = max(peak, equity)
        mdd = (equity - peak) / peak * 100 if peak else 0.0
        rows.append({"week": week, "trades": len(week_trades), "return_pct": pnl / initial_cash_krw * 100, "equity": equity, "mdd_pct": mdd})
    summary = {
        "schema_version": "v6",
        "months": months,
        "paper_entry_policy": paper_entry_policy,
        "initial_cash_krw": initial_cash_krw,
        "weekly_rows": rows,
        "weekly_trade_count": sum(row["trades"] for row in rows),
        "weekly_return_avg": sum(row["return_pct"] for row in rows) / len(rows) if rows else 0.0,
        "final_equity_krw": equity,
        "real_order_enabled": False,
        "live_order_allowed": False,
    }
    _write(Path("replay_store/v6_strategy/latest_v6_weekly_performance_summary.json"), summary)
    _write(Path("docs/reports/latest_v6_weekly_performance_summary.json"), summary)
    return summary


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
