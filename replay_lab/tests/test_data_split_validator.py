from __future__ import annotations

from validation.data_split_validator import split_trades_train_validation_test


def test_data_split_validator_splits_ordered_trades():
    trades = [{"trade_id": str(i), "entry_time": f"2026-01-{i+1:02d}", "pnl_krw": 100, "return_pct": 1.0} for i in range(10)]
    result = split_trades_train_validation_test(trades)
    assert result["split_counts"] == {"train": 6, "validation": 2, "test": 2}
    assert result["decision"] == "PASS"
