from execution.account_equity_tracker import AccountEquityTracker


def test_account_equity_tracker_records_curve_and_drawdown():
    tracker = AccountEquityTracker(500000)
    tracker.add(499000)
    summary = tracker.summary()
    assert summary["final_equity_krw"] == 499000
    assert summary["max_drawdown_pct"] < 0
