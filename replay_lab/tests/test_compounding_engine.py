from __future__ import annotations

from portfolio.compounding_engine import compound_trade_pnl, return_pct_from_equity


def test_compounding_engine_scales_with_equity():
    assert compound_trade_pnl(1000, 1000000, 500000) == 2000
    assert return_pct_from_equity(5000, 500000) == 1.0
