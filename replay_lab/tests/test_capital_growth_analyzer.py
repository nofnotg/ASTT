from __future__ import annotations

from analysis.capital_growth_analyzer import summarize_capital_growth
from portfolio.trade_journal_builder import build_trade_journal


def test_capital_growth_analyzer_returns_final_equity():
    summary = summarize_capital_growth(build_trade_journal()["journal"], 500000)
    assert summary["trade_count"] > 0
    assert summary["final_equity_krw"] > 0
