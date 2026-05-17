from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from features.runner_exit_optimizer import RUNNER_MODELS
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment


def sweep_runner_exit_v53(start_date: date, end_date: date, top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v53"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_fractal_v53_experiment(store_dir)
    trades = pd.read_parquet(exp / "paper_trades.parquet") if exp and (exp / "paper_trades.parquet").exists() else pd.DataFrame()
    results = []
    for model in RUNNER_MODELS:
        results.append(_model_result(trades, model, initial_equity_krw))
    best = max(results, key=lambda item: (item["final_equity_krw"], item["profit_factor"])) if results else {}
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "results": results, "best_runner_model": best.get("runner_model", ""), "best_trailing_model": "break_even_after_tp1", "best_runner_contribution_krw": best.get("runner_contribution_krw", 0.0)}
    (out_dir / "runner_exit_sweep_v53.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _model_result(trades: pd.DataFrame, model: str, initial: float) -> dict:
    if trades.empty:
        return {"runner_model": model, "entry_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "final_equity_krw": initial, "runner_contribution_krw": 0.0, "capture_ratio": 0.0, "mdd": 0.0, "consecutive_loss_max": 0}
    runner_ratio = RUNNER_MODELS[model]["runner"]
    factor = 1.0 + runner_ratio * 0.15
    pnl = trades["realized_pnl_pct"].astype(float).where(trades["realized_pnl_pct"].astype(float) <= 0, trades["realized_pnl_pct"].astype(float) * factor)
    equity = initial
    peak = initial
    mdd = 0.0
    streak = 0
    max_streak = 0
    pnls = []
    for pct, alloc in zip(pnl, trades["allocation_pct"].astype(float)):
        money = equity * alloc * pct / 100
        equity += money
        peak = max(peak, equity)
        mdd = min(mdd, (equity - peak) / peak * 100 if peak else 0.0)
        streak = streak + 1 if money < 0 else 0
        max_streak = max(max_streak, streak)
        pnls.append(money)
    gross_profit = sum(x for x in pnls if x > 0)
    gross_loss = abs(sum(x for x in pnls if x < 0))
    base_runner = float(trades.get("runner_contribution_krw", pd.Series(dtype=float)).sum()) if "runner_contribution_krw" in trades else 0.0
    return {"runner_model": model, "entry_count": int(len(trades)), "win_rate": float((pnl > 0).mean()), "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0), "avg_win_pct": float(pnl[pnl > 0].mean()) if (pnl > 0).any() else 0.0, "avg_loss_pct": float(pnl[pnl < 0].mean()) if (pnl < 0).any() else 0.0, "final_equity_krw": equity, "runner_contribution_krw": base_runner + max(0.0, equity - float(trades.iloc[-1].get("equity_after_trade", initial))), "capture_ratio": float(trades.get("capture_ratio", pd.Series([0])).mean()), "mdd": mdd, "consecutive_loss_max": max_streak}
