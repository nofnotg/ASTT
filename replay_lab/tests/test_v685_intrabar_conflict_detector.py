from __future__ import annotations

from atr_validation.intrabar_conflict_detector import detect_intrabar_conflict


def test_v685_intrabar_conflict_flags_unknown_order() -> None:
    row = {"entry_price": 100.0, "stop_price": 97.0, "target_price": 103.0, "exit_price": 101.0}
    result = detect_intrabar_conflict(row)
    assert result["bar_conflict"] is True
    assert result["conflict_type"] == "UNKNOWN_INTRABAR_ORDER"


def test_v685_intrabar_conflict_allows_wide_path() -> None:
    row = {"entry_price": 100.0, "stop_price": 80.0, "target_price": 130.0, "exit_price": 110.0}
    result = detect_intrabar_conflict(row)
    assert result["bar_conflict"] is False
    assert result["conflict_type"] == "NO_CONFLICT"
