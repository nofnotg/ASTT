from __future__ import annotations

import pytest

from bear_window.bear_window_performance import window_metrics, window_slice
from bear_window.bear_window_type_analyzer import type_summary


def test_v685_bear_window_performance_slices_and_scores_window() -> None:
    journal = [
        {"date": "2026-01-01", "equity_before": 100.0, "equity_after": 95.0, "pnl_krw": -5.0, "drawdown_pct": -5.0, "defense_action": "ENTER"},
        {"date": "2026-02-01", "equity_before": 95.0, "equity_after": 110.0, "pnl_krw": 15.0, "drawdown_pct": 0.0, "defense_action": "ENTER"},
    ]
    rows = window_slice(journal, "2026-01-01", "2026-01-31")
    metrics = window_metrics("TEST", rows, rows)
    assert metrics["trade_count"] == 1
    assert metrics["window_return_pct"] == pytest.approx(-5.0)
    assert metrics["window_mdd_pct"] == -5.0


def test_v685_bear_window_type_summary_uses_window_row_keys() -> None:
    rows = [{"type": "ignored", "window_type": "DRAWDOWN_WINDOW", "best_route": "R1", "best_return": -1.0, "mdd": -4.0}]
    summary = type_summary(rows)
    assert summary[0]["avg_return"] == -1.0
    assert summary[0]["avg_mdd"] == -4.0
