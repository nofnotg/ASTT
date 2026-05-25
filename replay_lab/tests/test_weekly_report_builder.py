from __future__ import annotations

from portfolio.trade_journal_builder import build_trade_journal
from portfolio.weekly_report_builder import build_weekly_rows


def test_weekly_report_builder_groups_trades():
    rows = build_weekly_rows(build_trade_journal()["journal"])
    assert rows
    assert "return_pct" in rows[0]
