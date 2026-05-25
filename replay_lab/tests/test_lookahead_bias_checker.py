from __future__ import annotations

from validation.lookahead_bias_checker import audit_trades_for_lookahead, check_trade_lookahead


def test_lookahead_bias_checker_flags_future_features():
    trade = {"trade_id": "t1", "entry_time": "2026-01-01 10:00:00", "exit_time": "2026-01-01 11:00:00", "feature_cutoff_time": "2026-01-01 10:01:00"}
    result = check_trade_lookahead(trade)
    assert result["lookahead_check"] == "FAIL"
    assert "FEATURE_CUTOFF_AFTER_ENTRY" in result["violations"]


def test_lookahead_audit_passes_normal_trade():
    trade = {"trade_id": "t1", "entry_time": "2026-01-01 10:00:00", "exit_time": "2026-01-01 11:00:00"}
    result = audit_trades_for_lookahead([trade])
    assert result["pass"] == 1
    assert result["fail"] == 0
