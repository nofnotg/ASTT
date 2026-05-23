from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.micro_execution_replay import latest_micro_execution_experiment


def validate_micro_exit(start_date: date, end_date: date, top_markets: int = 30, fixed_order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "micro_execution"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_micro_execution_experiment(store_dir)
    trades = pd.read_parquet(exp / "micro_trades.parquet") if exp and (exp / "micro_trades.parquet").exists() else pd.DataFrame()
    results = [_model(trades, fixed_order_krw, name) for name in ["FIXED_RR_EXIT", "MICRO_FAILURE_EXIT", "MICRO_TIME_STOP", "MICRO_TP_AND_FAILURE_EXIT"]]
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "results": results, "saved_loss_krw": _saved_loss(trades), "early_exit_missed_profit_krw": 0.0}
    (out_dir / "micro_exit_validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _model(trades: pd.DataFrame, order: float, name: str) -> dict:
    if trades.empty:
        return {"model": name, "entry_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "avg_win_pct": 0.0, "avg_loss_pct": 0.0, "expectancy_pct": 0.0, "avg_hold_seconds": 0.0, "micro_failure_exit_count": 0, "saved_loss_krw": 0.0, "early_exit_missed_profit_krw": 0.0}
    entered = trades[trades["entry_decision"] != "CANCEL"].copy()
    pnl = entered["realized_pnl_pct"].astype(float)
    if name == "FIXED_RR_EXIT":
        pnl = pnl.where(pnl > -0.8, -0.8)
    elif name == "MICRO_FAILURE_EXIT":
        pnl = pnl.where(entered["micro_exit_decision"] != "MICRO_FAILURE_EXIT", pnl.clip(lower=-0.25))
    elif name == "MICRO_TIME_STOP":
        pnl = pnl.where(entered["micro_exit_decision"] != "TIME_STOP", pnl * 0.8)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gp = float((wins / 100 * order).sum())
    gl = abs(float((losses / 100 * order).sum()))
    return {"model": name, "entry_count": int(len(entered)), "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0, "profit_factor": gp / gl if gl else (999.0 if gp else 0.0), "avg_win_pct": float(wins.mean()) if len(wins) else 0.0, "avg_loss_pct": float(losses.mean()) if len(losses) else 0.0, "expectancy_pct": float(pnl.mean()) if len(pnl) else 0.0, "avg_hold_seconds": float(entered["hold_seconds"].mean()) if "hold_seconds" in entered and len(entered) else 0.0, "micro_failure_exit_count": int((entered["micro_exit_decision"] == "MICRO_FAILURE_EXIT").sum()) if "micro_exit_decision" in entered else 0, "saved_loss_krw": 0.0, "early_exit_missed_profit_krw": 0.0}


def _saved_loss(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    micro = trades[trades.get("micro_exit_decision", "") == "MICRO_FAILURE_EXIT"]
    return float(abs(micro[micro["realized_pnl_pct"] < 0]["order_pnl_krw"].sum()))
