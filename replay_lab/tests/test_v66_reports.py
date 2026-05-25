from __future__ import annotations

import json

from replay_lab.feedback.v66_btcd_reports_html import V66BTCDRollingBalancedHTML


def test_v66_report_contains_korean_safety_text(tmp_path):
    payload = {
        "scenarios": [{"scenario": "CONTROL_EXISTING", "final_equity_krw": 1, "total_return_pct": 0, "mdd_pct": 0, "profit_factor": 1, "trade_count": 1, "return_mdd_ratio": 0, "decision": "LIVE_NOT_ALLOWED"}],
        "saved_loss_missed_profit": [],
        "yearly_comparison": [],
        "audit": {"checked_trades": 1, "pass": 1, "fail": 0, "excluded_trades": 0, "major_violations": []},
    }
    (tmp_path / "latest_v66_btcd_rolling_balanced_summary.json").write_text(json.dumps(payload), encoding="utf-8")

    V66BTCDRollingBalancedHTML(str(tmp_path)).build()
    html = (tmp_path / "latest_v66_btcd_rolling_balanced_report.html").read_text(encoding="utf-8")

    assert "실제 주문" in html
    assert "BTC Dominance" in html

