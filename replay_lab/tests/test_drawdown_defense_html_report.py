from __future__ import annotations

import json
from pathlib import Path

from replay_lab.feedback.drawdown_defense_html_report import DrawdownDefenseHTMLReport


def test_drawdown_defense_html_report_is_korean_utf8(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    payload = {
        "baseline_peak": {"time": "2025-05-13", "equity": 1434692},
        "baseline_trough": {"time": "2026-04-12", "equity": 799000, "drawdown_pct": -44.27},
        "selected_defense": {"scenario": "ROLLING_EDGE_THROTTLE", "capital": {"final_equity_krw": 1382279, "max_drawdown_pct": -15.37}},
        "scenarios": [
            {"scenario": "BASELINE", "capital": {"trade_count": 10, "final_equity_krw": 886330, "total_return_pct": 77.26, "max_drawdown_pct": -44.27}, "drawdown_window": {"total_pnl_krw": -631959, "throttled_trade_count": 0}},
            {"scenario": "ROLLING_EDGE_THROTTLE", "capital": {"trade_count": 10, "final_equity_krw": 1382279, "total_return_pct": 176.45, "max_drawdown_pct": -15.37}, "drawdown_window": {"total_pnl_krw": -225989, "throttled_trade_count": 5}},
        ],
        "diagnosis": {"trade_count": 10, "pnl_krw": -631959},
        "market_month_metrics": {},
    }
    (reports_dir / "latest_drawdown_defense_summary.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    result = DrawdownDefenseHTMLReport().build(str(reports_dir))
    html = Path(result["html"]).read_text(encoding="utf-8")

    assert "하락구간 방어 시스템 리포트" in html
    assert "최대 낙폭(MDD)" in html
    assert "\ufffd" not in html
