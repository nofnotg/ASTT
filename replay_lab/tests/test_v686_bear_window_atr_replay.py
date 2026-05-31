from __future__ import annotations

from analysis.v686_core import build_v686_bear_window_atr_replay_payload


def test_v686_bear_window_atr_replay_keeps_atr_data_insufficient(tmp_path) -> None:
    reports = tmp_path
    (reports / "latest_v684_bear_windows_summary.json").write_text('{"windows":[]}', encoding="utf-8")
    (reports / "latest_v686_atr_precision_v2_summary.json").write_text('{"final_atr_decision":"ATR_DATA_INSUFFICIENT"}', encoding="utf-8")
    payload = build_v686_bear_window_atr_replay_payload(500000.0, reports)
    assert payload["atr_final_decision"] == "ATR_DATA_INSUFFICIENT"
    assert payload["real_order_enabled"] is False
