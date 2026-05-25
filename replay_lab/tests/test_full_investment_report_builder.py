from __future__ import annotations

from portfolio.full_investment_report_builder import build_full_investment_summary
from portfolio.trade_journal_builder import build_trade_journal


def test_full_investment_report_builder_has_plain_language():
    summary = build_full_investment_summary(build_trade_journal()["journal"])
    assert "plain_language_summary" in summary
    assert summary["real_order_enabled"] is False
