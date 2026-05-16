from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.structure_reversal_v5 import StructureReversalV5Config, scan_structure_reversal_v5
from replay_lab.research.small_seed_metrics import summarize_trades


STACKS = {
    "No MTF": {"weekly": 0, "daily": 0, "h4": 0, "v5": 55, "ichimoku": False},
    "Daily Only": {"weekly": 0, "daily": 60, "h4": 0, "v5": 60, "ichimoku": False},
    "Daily + 4H": {"weekly": 0, "daily": 60, "h4": 55, "v5": 65, "ichimoku": False},
    "Weekly + Daily + 4H": {"weekly": 50, "daily": 60, "h4": 55, "v5": 70, "ichimoku": False},
    "Weekly + Daily + 4H + Ichimoku": {"weekly": 50, "daily": 60, "h4": 55, "v5": 70, "ichimoku": True},
}


def compare_mtf_context_v5(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, capital_krw: float = 500000, order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "structure_reversal_v5"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, thresholds in STACKS.items():
        config = StructureReversalV5Config(weekly_min_score=thresholds["weekly"], daily_min_score=thresholds["daily"], h4_min_score=thresholds["h4"], v5_min_score=thresholds["v5"], use_ichimoku=thresholds["ichimoku"])
        _, trades = scan_structure_reversal_v5(start_date, end_date, markets[:top_markets], capital_krw, order_krw, config, store_dir)
        if not trades.empty:
            trades = trades.sort_values(["date_kst", "v5_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(1)
        rows.append({"context_stack": name, **summarize_trades(trades.to_dict("records"), capital_krw)})
    best = max(rows, key=lambda row: (row.get("profit_factor", 0.0), row.get("account_return_pct", 0.0), row.get("entry_count", 0))) if rows else {}
    base = rows[0] if rows else {}
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "best_context_stack": best.get("context_stack", ""), "context_results": rows, "mtf_improvement": {"profit_factor_delta": best.get("profit_factor", 0.0) - base.get("profit_factor", 0.0), "mdd_delta": best.get("max_drawdown_pct", 0.0) - base.get("max_drawdown_pct", 0.0), "entry_count_delta": best.get("entry_count", 0) - base.get("entry_count", 0), "consecutive_loss_delta": best.get("consecutive_loss_max", 0) - base.get("consecutive_loss_max", 0)}}
    (out_dir / "mtf_context_compare_v5.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_parquet(out_dir / "mtf_context_compare_v5.parquet", index=False)
    return out_dir
