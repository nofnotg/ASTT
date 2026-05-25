from __future__ import annotations

from analysis.strategy_contribution_analyzer import analyze_strategy_contribution
from portfolio.trade_journal_builder import build_trade_journal


def test_strategy_contribution_analyzer_groups_by_strategy():
    rows = analyze_strategy_contribution(build_trade_journal()["journal"])
    assert rows
    assert "contribution_pct" in rows[0]
