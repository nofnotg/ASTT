from __future__ import annotations

import json
from pathlib import Path

from portfolio.causal_equity_defense_runner import run_causal_scenarios


def _journal() -> list[dict[str, object]]:
    rows = []
    for idx in range(35):
        pnl = 1000 if idx < 25 else -1000
        rows.append(
            {
                "trade_id": f"t{idx}",
                "entry_time": f"2025-01-{idx + 1:02d} 09:00:00",
                "exit_time": f"2025-01-{idx + 1:02d} 10:00:00",
                "feature_cutoff_time": f"2025-01-{idx + 1:02d} 09:00:00",
                "pnl_krw": pnl,
                "plan": "PLAN_A_ICT_FAT_TAIL",
                "strategy": "ICT_FVG_OB_SWEEP",
                "setup_type": "FVG_OB_OVERLAP",
                "regime": "ALT_ROTATION",
            }
        )
    return rows


def test_causal_runner_records_decision_time_and_lookahead_pass(tmp_path):
    source = tmp_path / "summary.json"
    source.write_text(json.dumps({"journal": _journal()}, ensure_ascii=False), encoding="utf-8")

    summary = run_causal_scenarios(source, 500000)

    balanced = next(row for row in summary["scenarios"] if row["scenario"] == "BALANCED_GROWTH")
    assert balanced["lookahead_fail_count"] == 0
    assert balanced["annotated_trade_sample"][0]["lookahead_check"] == "PASS"
    assert balanced["real_order_enabled"] is False
