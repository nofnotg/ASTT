from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.micro_execution_replay import latest_micro_execution_experiment


def simulate_latency_slippage(start_date: date, end_date: date, top_markets: int = 30, fixed_order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "micro_execution"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_micro_execution_experiment(store_dir)
    trades = pd.read_parquet(exp / "micro_trades.parquet") if exp and (exp / "micro_trades.parquet").exists() else pd.DataFrame()
    rows = []
    for latency in [0, 300, 500, 1000, 2000]:
        for slip in [0.0, 0.05, 0.10, 0.15, 0.25]:
            rows.append(_scenario(trades, fixed_order_krw, latency, slip))
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "results": rows, "break_even_slippage_pct": _break_even(rows), "latency_sensitive_trade_count": int((trades.get("hold_seconds", pd.Series(dtype=float)) <= 10).sum()) if not trades.empty else 0}
    (out_dir / "latency_slippage_simulation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _scenario(trades: pd.DataFrame, order: float, latency: int, slippage: float) -> dict:
    if trades.empty:
        return {"latency_ms": latency, "slippage_pct": slippage, "profit_factor": 0.0, "expectancy_pct": 0.0, "final_pnl_krw": 0.0}
    entered = trades[trades["entry_decision"] != "CANCEL"].copy()
    penalty = slippage + latency / 1000 * 0.01
    pnl = entered["realized_pnl_pct"].astype(float) - penalty
    gp = float((pnl[pnl > 0] / 100 * order).sum())
    gl = abs(float((pnl[pnl < 0] / 100 * order).sum()))
    return {"latency_ms": latency, "slippage_pct": slippage, "profit_factor": gp / gl if gl else (999.0 if gp else 0.0), "expectancy_pct": float(pnl.mean()) if len(pnl) else 0.0, "final_pnl_krw": float((pnl / 100 * order).sum())}


def _break_even(rows: list[dict]) -> float:
    profitable = [row["slippage_pct"] for row in rows if row["latency_ms"] == 0 and row["expectancy_pct"] > 0]
    return max(profitable) if profitable else 0.0
