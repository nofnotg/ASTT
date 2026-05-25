from __future__ import annotations

from replay_lab.research.head_controller_v62_review import run_head_controller_v62_review


def test_head_controller_v62_review_forces_no_live(tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "latest_v62_full_investment_summary.json").write_text('{"capital":{"trade_count":1},"risk":{"major_risk_flags":["OHLCV"]}}', encoding="utf-8")
    result = run_head_controller_v62_review(str(reports), "openai")
    assert result["live_order_allowed"] is False
    assert result["real_order_enabled"] is False
