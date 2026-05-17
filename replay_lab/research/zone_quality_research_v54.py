from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment


def research_zone_quality_v54(start_date: date, end_date: date, top_markets: int = 50, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "edge_isolation_v54"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_edge_isolation_v54_experiment(store_dir)
    trades = pd.read_parquet(exp / "edge_trades.parquet") if exp and (exp / "edge_trades.parquet").exists() else pd.DataFrame()
    grouped = []
    if not trades.empty:
        for grade, part in trades.groupby("zone_quality_grade"):
            grouped.append({"quality_grade": grade, "entry_count": int(len(part)), "win_rate": float((part["realized_pnl_pct"] > 0).mean()), "expectancy_pct": float(part["realized_pnl_pct"].mean()), "profit_factor": _pf(part)})
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "zone_count": int(len(trades)), "quality_grade_performance": grouped, "htf_overlap_effect": 0.0, "clean_retest_effect": 0.0, "zone_width_effect": 0.0, "reaction_history_effect": 0.0}
    (out_dir / "zone_quality_research_v54.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _pf(frame: pd.DataFrame) -> float:
    wins = frame[frame["realized_pnl_pct"] > 0]["realized_pnl_pct"].sum()
    losses = abs(frame[frame["realized_pnl_pct"] < 0]["realized_pnl_pct"].sum())
    return float(wins / losses) if losses else (999.0 if wins else 0.0)
