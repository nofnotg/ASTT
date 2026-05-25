from __future__ import annotations

from validation.rolling_window_integrity_checker import check_rolling_window_integrity


def test_rolling_window_integrity_fails_when_window_exceeds_prior_count():
    result = check_rolling_window_integrity([{"scenario": "X", "annotated_trade_sample": [{"trade_id": "t0", "rolling_trades_used": 1}]}])

    assert result["status"] == "FAIL"
