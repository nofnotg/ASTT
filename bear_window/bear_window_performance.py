from __future__ import annotations

from typing import Any

from bear_validation.metrics import profit_factor, saved_loss_vs


def window_slice(journal: list[dict[str, Any]], start_time: str, end_time: str) -> list[dict[str, Any]]:
    start_date = str(start_time)[:10]
    end_date = str(end_time)[:10]
    return [row for row in journal if start_date <= str(row.get("date", ""))[:10] <= end_date]


def window_metrics(name: str, rows: list[dict[str, Any]], active_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if not rows:
        base = {"scenario": name, "trade_count": 0, "window_pnl_krw": 0.0, "window_return_pct": 0.0, "window_mdd_pct": 0.0, "win_rate": 0.0, "PF": 0.0}
    else:
        start = float(rows[0].get("equity_before", 0.0))
        end = float(rows[-1].get("equity_after", 0.0))
        pnls = [float(row.get("pnl_krw", 0.0)) for row in rows if row.get("defense_action") == "ENTER"]
        base = {
            "scenario": name,
            "trade_count": len(pnls),
            "window_pnl_krw": end - start,
            "window_return_pct": (end / start - 1.0) * 100.0 if start else 0.0,
            "window_mdd_pct": min([0.0] + [float(row.get("drawdown_pct", 0.0)) for row in rows]),
            "win_rate": sum(1 for pnl in pnls if pnl > 0.0) / len(pnls) * 100.0 if pnls else 0.0,
            "PF": profit_factor(rows),
            "max_consecutive_losses": _max_loss_streak(pnls),
            "high_watermark_giveback": _giveback(rows),
        }
    if active_rows is not None:
        base.update(saved_loss_vs(rows, active_rows))
    return base


def _max_loss_streak(pnls: list[float]) -> int:
    best = cur = 0
    for pnl in pnls:
        cur = cur + 1 if pnl < 0.0 else 0
        best = max(best, cur)
    return best


def _giveback(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    equities = [float(row.get("equity_after", 0.0)) for row in rows]
    return max(equities) - equities[-1] if equities else 0.0
