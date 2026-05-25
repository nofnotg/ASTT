from __future__ import annotations

from portfolio.trade_journal_builder import build_trade_journal


def test_trade_journal_builder_outputs_required_fields():
    summary = build_trade_journal()
    row = summary["journal"][0]
    assert {"trade_id", "plan", "equity_before", "equity_after", "lesson"} <= set(row)
