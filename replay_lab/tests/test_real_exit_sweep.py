from __future__ import annotations

from analysis.real_exit_sweep import run_real_exit_sweep
from portfolio.trade_journal_builder import build_trade_journal


def test_real_exit_sweep_generates_exit_rules():
    rows = run_real_exit_sweep(build_trade_journal()["journal"])
    assert any(row["exit_rule"] == "PARTIAL_50_30_20" for row in rows)
