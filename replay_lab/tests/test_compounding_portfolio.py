from execution.compounding_portfolio import CompoundingPortfolio


def test_compounding_portfolio_updates_equity_and_drawdown():
    p = CompoundingPortfolio(500000)
    win = p.apply_trade_result({"allocation_pct": 0.8, "net_pnl_pct": 2})
    assert win["after_equity_krw"] == 508000
    loss = p.apply_trade_result({"allocation_pct": 1.0, "net_pnl_pct": -1})
    assert loss["max_drawdown_pct"] < 0
