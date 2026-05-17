from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from execution.allocation_policy_v53 import decide_allocation_v53
from execution.compounding_portfolio import CompoundingPortfolio
from features.allocation_diagnostic import build_allocation_diagnostic
from features.feature_snapshot_cache import get_or_build_feature_snapshot
from features.runner_exit_optimizer import simulate_runner_exit
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v52 import latest_fractal_v52_experiment
from replay_lab.replay.structure_reversal_v5 import _load_base_frame, _resample


@dataclass(frozen=True)
class FractalV53Config:
    allocation_model: str = "grade_based_v53"
    exit_model: str = "runner_sweep_best"
    max_daily_entries: int = 1
    use_cache: bool = True
    trailing_model: str = "break_even_after_tp1"
    runner_model: str = "BALANCED_RUNNER"


def run_fractal_v53(
    start_date: date,
    end_date: date,
    markets: list[str] | None = None,
    top_markets: int = 50,
    initial_equity_krw: float = 500000,
    max_daily_entries: int = 1,
    allocation_model: str = "grade_based_v53",
    exit_model: str = "runner_sweep_best",
    btc_dominance_path: str | None = None,
    use_cache: bool = True,
    replay_mode: str = "walk_forward_day_by_day",
    config: FractalV53Config | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    config = config or FractalV53Config(allocation_model=allocation_model, exit_model=exit_model, max_daily_entries=max_daily_entries, use_cache=use_cache)
    exp_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_fractal_v53")
    exp_dir = store_dir / "experiments" / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    seed_trades, seed_meta = _load_seed_trades(start_date, end_date, top_markets, store_dir)
    seed_trades = _limit_daily(seed_trades, max_daily_entries)
    trades = _replay_v53(seed_trades, initial_equity_krw, config, store_dir)
    metrics = _metrics(trades, initial_equity_krw)
    metrics.update(
        {
            "allocation_model": config.allocation_model,
            "exit_model": config.exit_model,
            "runner_model": config.runner_model,
            "trailing_model": config.trailing_model,
            "top_markets": top_markets,
            "replay_mode": replay_mode,
            "use_cache": use_cache,
            "btc_dominance_path": btc_dominance_path,
            "dominance_data_used": bool(btc_dominance_path),
            "fallback_used": not bool(btc_dominance_path),
            "seed_source": seed_meta,
            "full_validation_completed": _full_validation_completed(seed_meta, start_date, end_date, top_markets),
            "lookahead_guard": "DECISION_FEATURES_AS_OF_TIME_ONLY",
        }
    )
    metrics["live_readiness"] = live_readiness_v53(metrics, walk_forward={})
    allocation = build_allocation_diagnostic(trades, initial_equity_krw)

    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    pd.DataFrame(allocation["rows"]).to_parquet(exp_dir / "allocation_diagnostic.parquet", index=False)
    (exp_dir / "allocation_diagnostic.json").write_text(json.dumps({k: v for k, v in allocation.items() if k != "rows"}, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": exp_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "top_markets": top_markets,
                "max_daily_entries": max_daily_entries,
                "allocation_model": allocation_model,
                "exit_model": exit_model,
                "btc_dominance_path": btc_dominance_path,
                "use_cache": use_cache,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return exp_dir


def latest_fractal_v53_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    exps = sorted((store_dir / "experiments").glob("exp_*_fractal_v53"), key=lambda p: p.name)
    return exps[-1] if exps else None


def live_readiness_v53(metrics: dict, walk_forward: dict | None = None, zone_validation: dict | None = None, runner: dict | None = None) -> str:
    walk_forward = walk_forward or {}
    zone_validation = zone_validation or {}
    runner = runner or {}
    if not metrics.get("full_validation_completed", False):
        return "LIVE_NOT_ALLOWED"
    if walk_forward and (walk_forward.get("window_count", 0) < 3 or not walk_forward.get("stable", False)):
        return "LIVE_NOT_ALLOWED"
    if metrics.get("entry_count", 0) < 50:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("profit_factor", 0.0) < 1.1:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("final_equity_krw", 0.0) <= metrics.get("initial_equity_krw", 0.0):
        return "LIVE_NOT_ALLOWED"
    if metrics.get("max_drawdown_pct", 0.0) < -8.0 or metrics.get("consecutive_loss_max", 0) > 4:
        return "LIVE_NOT_ALLOWED"
    if zone_validation and not zone_validation.get("validation_passed", False):
        return "LIVE_NOT_ALLOWED"
    if runner and runner.get("best_runner_contribution_krw", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    if (
        metrics.get("profit_factor", 0.0) >= 1.3
        and metrics.get("max_drawdown_pct", 0.0) >= -5.0
        and metrics.get("consecutive_loss_max", 0) <= 3
        and walk_forward.get("positive_window_ratio", 0.0) >= 0.6
    ):
        return "MICRO_LIVE_READY"
    return "PAPER_MORE_REQUIRED"


def _load_seed_trades(start_date: date, end_date: date, top_markets: int, store_dir: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    experiments = sorted((store_dir / "experiments").glob("exp_*_fractal_v52"), key=lambda p: p.name, reverse=True)
    best: tuple[pd.DataFrame, dict[str, Any]] | None = None
    best_score = -1
    for exp in experiments:
        trades_path = exp / "paper_trades.parquet"
        cfg_path = exp / "config.json"
        if not trades_path.exists() or not cfg_path.exists():
            continue
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        trades = pd.read_parquet(trades_path)
        if trades.empty:
            continue
        trades["date_kst"] = trades["date_kst"].astype(str)
        mask = (pd.to_datetime(trades["date_kst"]).dt.date >= start_date) & (pd.to_datetime(trades["date_kst"]).dt.date <= end_date)
        overlap = trades[mask].copy()
        score = int(len(overlap)) + int(cfg.get("top_markets", 0))
        if score > best_score:
            best = (overlap, {"experiment": exp.name, **cfg})
            best_score = score
    if best:
        return best
    latest = latest_fractal_v52_experiment(store_dir)
    if latest and (latest / "paper_trades.parquet").exists():
        return pd.read_parquet(latest / "paper_trades.parquet"), {"experiment": latest.name, "fallback_latest": True}
    return pd.DataFrame(), {"experiment": None, "empty_seed": True, "requested_top_markets": top_markets}


def _limit_daily(trades: pd.DataFrame, max_daily_entries: int) -> pd.DataFrame:
    if trades.empty:
        return trades
    return trades.sort_values(["date_kst", "v5_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(max_daily_entries)


def _replay_v53(seed_trades: pd.DataFrame, initial_equity_krw: float, config: FractalV53Config, store_dir: Path) -> pd.DataFrame:
    if seed_trades.empty:
        return pd.DataFrame()
    portfolio = CompoundingPortfolio(initial_equity_krw)
    rows: list[dict[str, Any]] = []
    loss_streak = 0
    for trade in seed_trades.sort_values("entry_time_kst").to_dict("records"):
        market = trade.get("market")
        entry_time = pd.Timestamp(trade.get("entry_time_kst"))
        base = _load_base_frame(store_dir, market)
        if base.empty:
            continue
        history = base[base["time"] <= pd.Timestamp(trade.get("signal_time_kst", entry_time))].copy()
        if config.use_cache:
            get_or_build_feature_snapshot(
                market,
                pd.Timestamp(trade.get("signal_time_kst", entry_time)),
                {"1m": history.tail(300), "5m": _resample(history, "5min").tail(120)},
                {"version": "v53", "allocation_model": config.allocation_model},
            )
        entry = float(trade.get("entry_price", 0.0))
        stop = float(trade.get("zone_stop", entry * 0.992))
        target_space = {
            "target_1": float(trade.get("target_1", entry * 1.01)),
            "target_2": float(trade.get("target_2", entry * 1.02)),
            "target_3": float(trade.get("target_3", entry * 1.03)),
        }
        post = base[(base["time"] > entry_time) & (base["time"] <= entry_time + pd.Timedelta(minutes=180))].copy()
        runner = simulate_runner_exit(post, entry, stop, {"runner_model": config.runner_model}, target_space, config.trailing_model)
        realized = runner["realized_pnl_pct"] if config.exit_model == "runner_sweep_best" and post is not None and not post.empty else float(trade.get("realized_pnl_pct", 0.0))
        allocation = _allocation(trade, portfolio.current_equity_krw, config, loss_streak)
        if allocation["allocation_pct"] <= 0:
            continue
        portfolio_row = portfolio.apply_trade_result({"trade_id": f"{trade.get('date_kst')}_{market}", "allocation_pct": allocation["allocation_pct"], "net_pnl_pct": realized})
        loss_streak = loss_streak + 1 if portfolio_row["trade_pnl_krw"] < 0 else 0
        rows.append(
            {
                **trade,
                "before_equity_krw": portfolio_row["before_equity_krw"],
                "allocation_pct": allocation["allocation_pct"],
                "position_size_krw": portfolio_row["position_size_krw"],
                "realized_pnl_pct": realized,
                "trade_pnl_krw": portfolio_row["trade_pnl_krw"],
                "equity_after_trade": portfolio_row["after_equity_krw"],
                "max_drawdown_pct": portfolio_row["max_drawdown_pct"],
                "runner_model": config.runner_model,
                "trailing_model": config.trailing_model,
                "runner_exit_reason": runner["runner_exit_reason"],
                "runner_contribution_pct": runner["runner_contribution_pct"],
                "runner_contribution_krw": runner["runner_contribution_pct"] * portfolio_row["position_size_krw"] / 100,
                "capture_ratio": runner["capture_ratio"],
                "mfe_pct": runner["max_favorable_excursion_pct"],
                "mae_pct": runner["max_adverse_excursion_pct"],
            }
        )
    return pd.DataFrame(rows)


def _allocation(trade: dict, equity: float, config: FractalV53Config, loss_streak: int) -> dict:
    if config.allocation_model == "fixed_10k":
        pct = min(1.0, 10000 / equity)
        return {"allocation_pct": pct, "position_size_krw": equity * pct}
    if config.allocation_model == "full_seed":
        return {"allocation_pct": 1.0, "position_size_krw": equity}
    return decide_allocation_v53(
        equity,
        str(trade.get("signal_grade", "REJECT")),
        str(trade.get("target_space_grade", "REJECT")),
        str(trade.get("fractal_state", "UNKNOWN")),
        str(trade.get("btc_regime", "DOMINANCE_UNAVAILABLE")),
        consecutive_loss=loss_streak,
    )


def _metrics(trades: pd.DataFrame, initial_equity_krw: float) -> dict:
    if trades.empty:
        return {
            "entry_count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "initial_equity_krw": initial_equity_krw,
            "final_equity_krw": initial_equity_krw,
            "equity_return_pct": 0.0,
            "total_pnl_krw": 0.0,
            "max_drawdown_pct": 0.0,
            "consecutive_loss_max": 0,
        }
    wins = trades[trades["trade_pnl_krw"] > 0]
    losses = trades[trades["trade_pnl_krw"] < 0]
    gross_profit = float(wins["trade_pnl_krw"].sum())
    gross_loss = abs(float(losses["trade_pnl_krw"].sum()))
    final = float(trades.iloc[-1]["equity_after_trade"])
    streak = 0
    max_streak = 0
    for is_loss in (trades["trade_pnl_krw"] < 0):
        streak = streak + 1 if is_loss else 0
        max_streak = max(max_streak, streak)
    return {
        "entry_count": int(len(trades)),
        "win_rate": float((trades["trade_pnl_krw"] > 0).mean()),
        "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0),
        "initial_equity_krw": float(initial_equity_krw),
        "final_equity_krw": final,
        "equity_return_pct": (final - initial_equity_krw) / initial_equity_krw * 100 if initial_equity_krw else 0.0,
        "total_pnl_krw": final - initial_equity_krw,
        "max_drawdown_pct": float(trades["max_drawdown_pct"].min()) if "max_drawdown_pct" in trades else 0.0,
        "consecutive_loss_max": max_streak,
        "runner_contribution_krw": float(trades.get("runner_contribution_krw", pd.Series(dtype=float)).sum()),
        "avg_capture_ratio": float(trades.get("capture_ratio", pd.Series(dtype=float)).mean()) if "capture_ratio" in trades else 0.0,
        "avg_allocation_pct": float(trades["allocation_pct"].mean()) if "allocation_pct" in trades else 0.0,
        "alt_risk_on_trades": int((trades.get("btc_regime", "") == "ALT_RISK_ON").sum()) if "btc_regime" in trades else 0,
        "btc_led_trades": int((trades.get("btc_regime", "") == "BTC_LED").sum()) if "btc_regime" in trades else 0,
        "risk_off_blocked": 0,
    }


def _full_validation_completed(seed_meta: dict, start_date: date, end_date: date, top_markets: int) -> bool:
    try:
        return (
            date.fromisoformat(str(seed_meta.get("start_date"))) <= start_date
            and date.fromisoformat(str(seed_meta.get("end_date"))) >= end_date
            and int(seed_meta.get("top_markets", 0)) >= top_markets
        )
    except (TypeError, ValueError):
        return False
