from __future__ import annotations

from typing import Any, Callable


def replay_with_fill_model(source: list[dict[str, Any]], initial_cash_krw: float, model_name: str, pnl_fn: Callable[[dict[str, Any]], float]) -> list[dict[str, Any]]:
    equity = initial_cash_krw
    peak = initial_cash_krw
    out = []
    for row in source:
        before = equity
        pnl = pnl_fn(row)
        equity = max(0.0, equity + pnl)
        peak = max(peak, equity)
        new = dict(row)
        new.update(
            {
                "scenario": model_name,
                "equity_before": before,
                "equity_after": equity,
                "pnl_krw": pnl,
                "drawdown_pct": (equity / peak - 1.0) * 100.0 if peak else 0.0,
            }
        )
        out.append(new)
    return out
