from __future__ import annotations

from atr_precision_v2.atr_ltf_replayer import replay_trade_with_ltf
from atr_precision_v2.atr_path_schema import ATRReplayConfig


def test_v686_atr_ltf_replay_resolves_conservative_same_bar_to_stop() -> None:
    trade = {"trade_id": "T1", "market": "KRW-BTC", "entry_price": 100.0, "stop_price": 98.0, "target_price": 103.0, "position_krw": 100000.0}
    bars = [{"timestamp": "2026-01-01 00:01:00", "open": 100.0, "high": 104.0, "low": 97.0, "close": 101.0}]
    result = replay_trade_with_ltf(trade, bars, ATRReplayConfig(fill_model="conservative"))
    assert result["ltf_available"] is True
    assert result["same_bar_conflict"] is True
    assert result["exit_reason"] == "STOP_SAME_BAR_CONSERVATIVE"


def test_v686_atr_ltf_replay_marks_missing_data() -> None:
    result = replay_trade_with_ltf({"trade_id": "T1", "market": "KRW-BTC"}, [], ATRReplayConfig())
    assert result["decision"] == "ATR_DATA_INSUFFICIENT"
