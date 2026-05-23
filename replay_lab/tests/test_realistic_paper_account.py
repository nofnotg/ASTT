from execution.realistic_paper_account import RealisticPaperAccount


def test_realistic_paper_account_open_close_and_pnl():
    acct = RealisticPaperAccount(initial_cash_krw=500000, fixed_order_krw=10000)
    pos = acct.open_position({"market": "KRW-BTC", "order_krw": 10000}, {"fill_price": 100, "fee_krw": 5})
    closed = acct.close_position(pos["position_id"], {"fill_price": 101, "fee_krw": 5}, "TAKE_PROFIT")
    assert closed["pnl_krw"] > 0
    assert acct.summary()["trade_count"] == 1
    assert "max_drawdown_pct" in acct.summary()
