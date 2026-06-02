from __future__ import annotations

import json
from pathlib import Path

from analysis.v687_investment_pattern_validator import run_v687_investment_pattern_validation


def test_v687_investment_pattern_validator_writes_summary(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    reports = tmp_path / "docs" / "reports"
    journal = tmp_path / "data" / "paper" / "journal"
    reports.mkdir(parents=True)
    journal.mkdir(parents=True)
    (reports / "latest_v683_backfill_20260101_summary.json").write_text(
        json.dumps(
            {
                "run_id": "r1",
                "active_route": "ACTIVE",
                "monthly_returns": {
                    "ACTIVE": [{"period": "2026-02", "return_pct": -6.0, "mdd_pct": -12.0}],
                    "SHADOW": [{"period": "2026-02", "return_pct": -2.0, "mdd_pct": -7.0}],
                },
                "active_vs_shadow_monthly": [{"month": "2026-02", "comment": "shadow stronger"}],
            }
        ),
        encoding="utf-8",
    )
    trade_lines = []
    decision_lines = []
    for idx in range(6):
        trade_id = f"r1:ACTIVE:t{idx}"
        pnl = 1000 if idx % 2 == 0 else -500
        trade_lines.append(
            json.dumps(
                {
                    "trade_id": trade_id,
                    "market": "KRW-BTC",
                    "entry_time": f"2026-02-0{idx + 1} 01:00:00",
                    "size_krw": 10000,
                    "realized_pnl_krw": pnl,
                    "pnl_pct": pnl / 10000 * 100,
                }
            )
        )
        decision_lines.append(
            json.dumps(
                {
                    "decision_id": trade_id,
                    "decision_time": f"2026-02-0{idx + 1} 01:00:00",
                    "market_state": "NORMAL",
                    "action": "ENTER_REDUCED_35",
                    "pf20": 1.1,
                    "month_return_pct": -1.0,
                    "hwm_drawdown_pct": -11.0,
                    "dominance_risk": False,
                    "reason": ["ROLLING_EDGE_THROTTLE"],
                }
            )
        )
    (journal / "paper_trades.jsonl").write_text("\n".join(trade_lines), encoding="utf-8")
    (journal / "paper_decisions.jsonl").write_text("\n".join(decision_lines), encoding="utf-8")

    result = run_v687_investment_pattern_validation(reports, tmp_path / "data" / "paper")

    assert result["live_order_allowed"] is False
    assert result["data_range"]["trade_count"] == 6
    assert result["february_feedback"]["best_february_route"]["route_id"] == "SHADOW"
    assert result["risk_reward_patterns"]
    assert (reports / "latest_v687_investment_pattern_validation_summary.json").exists()
