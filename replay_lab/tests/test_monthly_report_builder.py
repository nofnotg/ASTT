from __future__ import annotations

from portfolio.monthly_report_builder import build_monthly_rows
from portfolio.trade_journal_builder import build_trade_journal


def test_monthly_report_builder_groups_trades():
    rows = build_monthly_rows(build_trade_journal()["journal"])
    assert rows
    assert "profit_factor" in rows[0]
