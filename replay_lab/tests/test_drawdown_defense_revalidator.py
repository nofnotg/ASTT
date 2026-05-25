from __future__ import annotations

import json
from pathlib import Path

from analysis.drawdown_defense_revalidator import run_drawdown_defense_revalidation


def _trade(idx: int, pnl: float) -> dict[str, object]:
    day = idx + 1
    return {
        "trade_id": f"t{idx}",
        "market": "KRW-BTC",
        "plan": "PLAN_A_ICT_FAT_TAIL",
        "strategy": "ICT_FVG_OB_SWEEP",
        "setup_type": "FVG_LIQUIDITY_SWEEP",
        "entry_time": f"2025-01-{day:02d} 09:00:00",
        "exit_time": f"2025-01-{day:02d} 10:00:00",
        "pnl_krw": pnl,
    }


def test_drawdown_defense_revalidation_writes_selected_rolling_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source_path = Path("docs/reports/latest_true_walk_forward_summary.json")
    source_path.parent.mkdir(parents=True)
    journal = [_trade(idx, 10000) for idx in range(5)] + [_trade(idx + 5, -10000) for idx in range(25)]
    source_path.write_text(json.dumps({"journal": journal}, ensure_ascii=False), encoding="utf-8")

    result = run_drawdown_defense_revalidation(source_path, "empty_archive", 500000)

    assert result["selected_defense"]["scenario"] == "ROLLING_EDGE_THROTTLE"
    assert result["selected_defense"]["capital"]["final_equity_krw"] > result["scenarios"][0]["capital"]["final_equity_krw"]
    assert result["real_order_enabled"] is False
    assert Path("docs/reports/latest_drawdown_defense_summary.json").exists()
