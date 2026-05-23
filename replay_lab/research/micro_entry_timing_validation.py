from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.micro_execution_replay import latest_micro_execution_experiment


def validate_micro_entry_timing(start_date: date, end_date: date, top_markets: int = 30, fixed_order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "micro_execution"
    out_dir.mkdir(parents=True, exist_ok=True)
    trades = _latest_trades(store_dir)
    results = [
        _summary("MINUTE_ENTRY", trades, fixed_order_krw, cancel_filter=False),
        _summary("MICRO_CONFIRM_ENTRY", trades[trades["entry_decision"] != "CANCEL"] if not trades.empty else trades, fixed_order_krw, cancel_filter=True),
        _summary("MICRO_CANCEL_BAD_ENTRY", trades, fixed_order_krw, cancel_filter=True),
    ]
    minute_losses = set(trades[(trades["realized_pnl_pct"] < 0)].index) if not trades.empty else set()
    cancelled = set(trades[trades["entry_decision"] == "CANCEL"].index) if not trades.empty and "entry_decision" in trades else set()
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "results": results, "avoided_loss_count": len(minute_losses & cancelled), "missed_win_count": int(((trades.get("entry_decision", "") == "CANCEL") & (trades.get("realized_pnl_pct", 0) > 0)).sum()) if not trades.empty else 0, "net_improvement_krw": 0.0}
    (out_dir / "micro_entry_timing_validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _latest_trades(store_dir: Path) -> pd.DataFrame:
    exp = latest_micro_execution_experiment(store_dir)
    return pd.read_parquet(exp / "micro_trades.parquet") if exp and (exp / "micro_trades.parquet").exists() else pd.DataFrame()


def _summary(model: str, trades: pd.DataFrame, order: float, cancel_filter: bool) -> dict:
    if trades.empty:
        return {"model": model, "entry_count": 0, "cancel_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_pct": 0.0, "avg_entry_delay_seconds": 0.0, "avoided_loss_count": 0, "missed_win_count": 0, "net_improvement_krw": 0.0}
    entered = trades[trades["entry_decision"] != "CANCEL"] if cancel_filter else trades
    pnl = entered["realized_pnl_pct"].astype(float)
    gp = float((pnl[pnl > 0] / 100 * order).sum())
    gl = abs(float((pnl[pnl < 0] / 100 * order).sum()))
    return {"model": model, "entry_count": int(len(entered)), "cancel_count": int((trades["entry_decision"] == "CANCEL").sum()), "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0, "profit_factor": gp / gl if gl else (999.0 if gp else 0.0), "expectancy_pct": float(pnl.mean()) if len(pnl) else 0.0, "avg_entry_delay_seconds": 0.0, "avoided_loss_count": 0, "missed_win_count": 0, "net_improvement_krw": float(entered["order_pnl_krw"].sum()) if "order_pnl_krw" in entered else 0.0}
