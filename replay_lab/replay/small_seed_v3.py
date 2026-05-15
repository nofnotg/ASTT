from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.preopen_confirmed_compare import evaluate_entry_mode
from replay_lab.research.small_seed_metrics import aggregate_small_seed_daily, aggregate_small_seed_monthly, aggregate_small_seed_weekly, summarize_trades
from replay_lab.research.threshold_sweep_v3 import build_v3_candidate_outcomes, filter_candidates_by_threshold


def run_small_seed_v3(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    max_daily_entries: int = 1,
    top_markets: int = 50,
    strategy_mode: str = "confirmed",
    selected_windows: list[str] | None = None,
    threshold_config: dict | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_small_seed_v3")
    exp_dir = store_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    selected_markets = markets[:top_markets] if top_markets else markets
    config = {
        "experiment_id": experiment_id,
        "mode": "SMALL_SEED_V3",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "max_daily_entries": max_daily_entries,
        "top_markets": top_markets,
        "strategy_mode": strategy_mode,
        "selected_windows": selected_windows or ["09:00"],
        "threshold_config": threshold_config or {},
    }
    (exp_dir / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    if strategy_mode == "confirmed":
        trades = evaluate_entry_mode("confirmed", start_date, end_date, selected_markets, capital_krw, order_krw, store_dir)["trades"]
    elif strategy_mode == "preopen":
        trades = evaluate_entry_mode("preopen", start_date, end_date, selected_markets, capital_krw, order_krw, store_dir)["trades"]
    else:
        candidates = build_v3_candidate_outcomes(start_date, end_date, capital_krw, order_krw, top_markets, store_dir)
        trades = filter_candidates_by_threshold(candidates, threshold_config or {"final_score": 70, "setup_score": 65, "trigger_score": 65, "confidence": 50})

    trades = trades.copy() if isinstance(trades, pd.DataFrame) else pd.DataFrame(trades)
    if not trades.empty:
        trades = trades.sort_values(["date_kst", "order_pnl_krw"], ascending=[True, False]).groupby("date_kst", as_index=False).head(max_daily_entries)
        trades["strategy_mode"] = strategy_mode
        trades["experiment_id"] = experiment_id

    daily = aggregate_small_seed_daily(trades.to_dict("records"), capital_krw)
    weekly = aggregate_small_seed_weekly(daily, capital_krw)
    monthly = aggregate_small_seed_monthly(daily, capital_krw)
    metrics = {
        **summarize_trades(trades.to_dict("records"), capital_krw),
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "strategy_mode": strategy_mode,
        "live_readiness": live_readiness(summarize_trades(trades.to_dict("records"), capital_krw)),
    }
    decisions = _decisions_from_trades(trades, start_date, end_date, experiment_id, strategy_mode)

    decisions.to_parquet(exp_dir / "decisions.parquet", index=False)
    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    daily.to_parquet(exp_dir / "daily_account.parquet", index=False)
    weekly.to_parquet(exp_dir / "weekly_account.parquet", index=False)
    monthly.to_parquet(exp_dir / "monthly_account.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "report.md").write_text(_markdown_summary(metrics), encoding="utf-8")
    return exp_dir


def live_readiness(metrics: dict, critical_data_quality_warning: bool = False) -> str:
    if critical_data_quality_warning:
        return "LIVE_NOT_ALLOWED"
    if (
        metrics.get("entry_count", 0) >= 50
        and metrics.get("account_return_pct", 0.0) > 0
        and metrics.get("max_drawdown_pct", 0.0) >= -8.0
        and metrics.get("consecutive_loss_max", 999) <= 3
        and metrics.get("profit_factor", 0.0) >= 1.1
    ):
        return "MICRO_LIVE_READY"
    if (
        metrics.get("account_return_pct", 0.0) < 0
        or metrics.get("profit_factor", 0.0) < 0.9
        or metrics.get("consecutive_loss_max", 0) >= 4
    ):
        return "LIVE_NOT_ALLOWED"
    if metrics.get("entry_count", 0) >= 20:
        return "PAPER_MORE_REQUIRED"
    return "LIVE_NOT_ALLOWED"


def latest_small_seed_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    experiments = sorted((store_dir / "experiments").glob("exp_*_small_seed_v3"), key=lambda path: path.name)
    return experiments[-1] if experiments else None


def _decisions_from_trades(trades: pd.DataFrame, start_date: date, end_date: date, experiment_id: str, strategy_mode: str) -> pd.DataFrame:
    trade_dates = set(trades["date_kst"].astype(str)) if not trades.empty and "date_kst" in trades else set()
    rows: list[dict[str, Any]] = []
    day = start_date
    while day <= end_date:
        day_s = day.isoformat()
        day_trade = trades[trades["date_kst"].astype(str) == day_s].iloc[0] if day_s in trade_dates else None
        rows.append(
            {
                "experiment_id": experiment_id,
                "date_kst": day_s,
                "strategy_mode": strategy_mode,
                "entered": day_trade is not None,
                "market": str(day_trade.get("market", "")) if day_trade is not None else "",
                "decision": "ENTER" if day_trade is not None else "HOLD",
                "reason": "selected by V3 small-seed runner" if day_trade is not None else "no eligible V3 candidate",
            }
        )
        day = day.fromordinal(day.toordinal() + 1)
    return pd.DataFrame(rows)


def _markdown_summary(metrics: dict) -> str:
    return f"""# ASTT V3 Small Seed Result

- strategy_mode: {metrics.get("strategy_mode")}
- capital_krw: {metrics.get("capital_krw"):,.0f}
- order_krw: {metrics.get("order_krw"):,.0f}
- entry_count: {metrics.get("entry_count")}
- win_rate: {metrics.get("win_rate", 0) * 100:.2f}%
- total_order_pnl_krw: {metrics.get("total_order_pnl_krw", 0):,.0f}
- account_return_pct: {metrics.get("account_return_pct", 0):.4f}%
- max_drawdown_pct: {metrics.get("max_drawdown_pct", 0):.4f}%
- consecutive_loss_max: {metrics.get("consecutive_loss_max")}
- profit_factor: {metrics.get("profit_factor", 0):.4f}
- live_readiness: {metrics.get("live_readiness")}
"""
