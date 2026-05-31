from __future__ import annotations

from atr_ltf.ltf_coverage_analyzer import analyze_ltf_coverage


def test_v686_ltf_coverage_does_not_generate_fake_data(tmp_path) -> None:
    trades = [{"trade_id": "T1", "market": "KRW-BTC", "entry_time": "2026-01-01 00:00:00", "exit_time": "2026-01-01 01:00:00"}]
    result = analyze_ltf_coverage(trades, [tmp_path])
    assert result["total_atr_trades"] == 1
    assert result["uncovered"] == 1
    assert result["fake_data_generated"] is False
    assert result["decision"] == "ATR_DATA_INSUFFICIENT"
