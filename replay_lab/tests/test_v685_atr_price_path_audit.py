from __future__ import annotations

from atr_validation.atr_report_builder import atr_decision
from atr_validation.lower_timeframe_replay import lower_timeframe_coverage
from atr_validation.price_path_auditor import build_price_path_rows


def test_v685_price_path_audit_requires_lower_timeframe_for_conflict() -> None:
    journal = [
        {
            "trade_id": "T1",
            "market": "KRW-BTC",
            "entry_time": "2026-01-01T00:00:00",
            "exit_time": "2026-01-01T01:00:00",
            "entry_price": 100.0,
            "stop_price": 97.0,
            "target_price": 103.0,
        }
    ]
    rows = build_price_path_rows(journal)
    coverage = lower_timeframe_coverage(journal)
    assert rows[0]["decision"] == "REQUIRES_1M_REPLAY"
    assert coverage["lower_timeframe_available"] is False
    assert atr_decision([], coverage["lower_timeframe_available"]) == "ATR_RESEARCH_ONLY_PRICE_PATH_REQUIRED"
