from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from execution.compounding_portfolio import CompoundingPortfolio
from execution.full_seed_risk_gate import evaluate_full_seed_risk_gate
from features.btc_dominance import compute_btc_dominance_regime
from features.dynamic_exit_plan import build_dynamic_exit_plan
from features.fractal_mtf_context import compute_fractal_mtf_context
from features.position_sizing import decide_position_size
from features.supply_demand_zone import detect_supply_demand_zones
from features.target_space import compute_target_space
from features.weekly_power import compute_weekly_power
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.structure_reversal_v5 import StructureReversalV5Config, _load_base_frame, _resample, scan_structure_reversal_v5
from replay_lab.research.small_seed_metrics import summarize_trades


@dataclass(frozen=True)
class FractalV52Config:
    allocation_model: str = "grade_based"
    exit_model: str = "partial_tp_runner"
    max_daily_entries: int = 1
    use_btc_dominance: bool = True
    use_zone_engine: bool = True
    use_full_seed_compounding: bool = True


def run_fractal_v52(
    start_date: date,
    end_date: date,
    markets: list[str],
    top_markets: int = 50,
    initial_equity_krw: float = 500000,
    max_daily_entries: int = 1,
    strategy_modes: list[str] | None = None,
    use_btc_dominance: bool = True,
    use_zone_engine: bool = True,
    use_full_seed_compounding: bool = True,
    replay_mode: str = "walk_forward_day_by_day",
    allocation_model: str = "grade_based",
    exit_model: str = "partial_tp_runner",
    config: FractalV52Config | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    config = config or FractalV52Config(allocation_model=allocation_model, exit_model=exit_model, max_daily_entries=max_daily_entries, use_btc_dominance=use_btc_dominance, use_zone_engine=use_zone_engine, use_full_seed_compounding=use_full_seed_compounding)
    exp_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_fractal_v52")
    exp_dir = store_dir / "experiments" / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    candidates, base_trades = scan_structure_reversal_v5(start_date, end_date, markets[:top_markets], initial_equity_krw, 10000, StructureReversalV5Config(max_daily_entries=max_daily_entries), store_dir)
    if not base_trades.empty:
        base_trades = base_trades.sort_values(["date_kst", "v5_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(max_daily_entries)
    trades = enrich_trades_v52(base_trades, store_dir, initial_equity_krw, config)
    metrics = _metrics(trades, initial_equity_krw)
    metrics.update({"initial_equity_krw": initial_equity_krw, "allocation_model": config.allocation_model, "exit_model": config.exit_model, "candidate_count": int(len(candidates)), "replay_mode": replay_mode, "lookahead_guard": "AS_OF_TIME_FILTERED", "live_readiness": live_readiness_v52(metrics, full_period_completed=False, walk_forward_completed=False)})
    candidates.to_parquet(exp_dir / "candidates.parquet", index=False)
    base_trades.to_parquet(exp_dir / "base_trades.parquet", index=False)
    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "config.json").write_text(json.dumps({"experiment_id": exp_id, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "top_markets": top_markets, **asdict(config)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def enrich_trades_v52(base_trades: pd.DataFrame, store_dir: Path, initial_equity_krw: float, config: FractalV52Config) -> pd.DataFrame:
    if base_trades.empty:
        return pd.DataFrame()
    portfolio = CompoundingPortfolio(initial_equity_krw)
    rows: list[dict[str, Any]] = []
    btc = _load_base_frame(store_dir, "KRW-BTC")
    consecutive_loss = 0
    for trade in base_trades.sort_values("entry_time_kst").to_dict("records"):
        market = trade["market"]
        as_of = pd.Timestamp(trade["signal_time_kst"])
        base = _load_base_frame(store_dir, market)
        history = base[base["time"] <= as_of].copy()
        if history.empty:
            continue
        tf = {"1m": history, "5m": _resample(history, "5min"), "15m": _resample(history, "15min"), "1h": _resample(history, "60min"), "4h": _resample(history, "240min"), "1d": _resample(history, "1D"), "1w": _resample(history, "1W")}
        weekly = compute_weekly_power(tf["1w"].iloc[:-1], tf["1w"].tail(1), tf["1d"], as_of)
        fractal = compute_fractal_mtf_context(weekly, {"daily_structure_score": trade.get("daily_structure_score", 0)}, {"h4_flow_score": trade.get("h4_flow_score", 0)}, {"score": trade.get("v5_score", 0)}, {"score": trade.get("v5_score", 0)}, {"score": trade.get("v5_score", 0)})
        btc_regime = compute_btc_dominance_regime(btc, None, krw_breadth=0.5, as_of_time=as_of) if config.use_btc_dominance else {"alt_regime": "DISABLED", "alt_long_allowed": True, "position_size_multiplier": 1.0, "warnings": []}
        zones = detect_supply_demand_zones(tf["15m"], "15m", as_of_time=as_of) if config.use_zone_engine else []
        entry = float(trade["entry_price"])
        stop = entry * 0.992
        above = [z for z in zones if z["zone_low"] > entry]
        below = [z for z in zones if z["zone_high"] < entry]
        target = compute_target_space(entry, stop, above, below, fractal)
        risk = evaluate_full_seed_risk_gate({"btc_regime": btc_regime, "target_space": target, "zone_width_pct": zones[0]["zone_width_pct"] if zones else 0.0, "consecutive_loss": consecutive_loss, "data_quality": "GOOD"})
        signal_grade = _signal_grade(float(trade.get("v5_score", 0)), target["target_space_grade"])
        sizing = decide_position_size(portfolio.current_equity_krw, signal_grade, target["target_space_grade"], fractal, btc_regime, risk)
        if config.allocation_model == "fixed_10k":
            sizing["allocation_pct"] = min(1.0, 10000 / portfolio.current_equity_krw)
            sizing["position_size_krw"] = portfolio.current_equity_krw * sizing["allocation_pct"]
        elif config.allocation_model == "full_seed" and risk["risk_decision"] != "REJECT":
            sizing["allocation_pct"] = min(1.0, risk["max_allowed_allocation_pct"])
            sizing["position_size_krw"] = portfolio.current_equity_krw * sizing["allocation_pct"]
        exit_plan = build_dynamic_exit_plan(entry, stop, target, fractal, signal_grade)
        realized = float(trade.get("net_signal_pnl_pct", trade.get("gross_signal_pnl_pct", 0.0)))
        if risk["risk_decision"] == "REJECT" or sizing["allocation_pct"] <= 0:
            continue
        portfolio_row = portfolio.apply_trade_result({"trade_id": f"{trade['date_kst']}_{market}", "allocation_pct": sizing["allocation_pct"], "net_pnl_pct": realized})
        consecutive_loss = consecutive_loss + 1 if portfolio_row["trade_pnl_krw"] < 0 else 0
        rows.append({**trade, "weekly_state": weekly["weekly_state"], "fractal_alignment_score": fractal["fractal_alignment_score"], "fractal_state": fractal["fractal_state"], "btc_regime": btc_regime["alt_regime"], "dominance_state": "UNAVAILABLE" if "dominance_unavailable" in btc_regime.get("warnings", []) else "AVAILABLE", "zone_entry": zones[0]["zone_mid"] if zones else 0.0, "zone_stop": stop, "target_1": target["target_1"], "target_2": target["target_2"], "target_3": target["target_3"], "risk_pct": target["risk_pct"], "target_space_pct": target["max_target_space_pct"], "risk_reward_1": target["risk_reward_1"], "risk_reward_2": target["risk_reward_2"], "signal_grade": signal_grade, "allocation_pct": sizing["allocation_pct"], "position_size_krw": sizing["position_size_krw"], "exit_plan": exit_plan["exit_style"], "realized_pnl_pct": realized, "trade_pnl_krw": portfolio_row["trade_pnl_krw"], "equity_after_trade": portfolio_row["after_equity_krw"], "max_drawdown_pct": portfolio_row["max_drawdown_pct"], "target_space_grade": target["target_space_grade"], "runner_ratio": exit_plan["runner_ratio"], "trailing_enabled": exit_plan["trailing_stop"].get("enabled", False), "risk_veto_reasons": "|".join(risk["veto_reasons"])})
    return pd.DataFrame(rows)


def live_readiness_v52(metrics: dict, full_period_completed: bool, walk_forward_completed: bool) -> str:
    if not full_period_completed or not walk_forward_completed:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("entry_count", 0) < 30 or metrics.get("profit_factor", 0) < 1.1 or metrics.get("final_equity_krw", 0) <= metrics.get("initial_equity_krw", 0) or metrics.get("consecutive_loss_max", 0) > 4:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("entry_count", 0) >= 50 and metrics.get("profit_factor", 0) >= 1.3 and metrics.get("max_drawdown_pct", 0) >= -5 and metrics.get("consecutive_loss_max", 0) <= 3:
        return "MICRO_LIVE_READY"
    return "PAPER_MORE_REQUIRED"


def latest_fractal_v52_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    exps = sorted((store_dir / "experiments").glob("exp_*_fractal_v52"), key=lambda p: p.name)
    return exps[-1] if exps else None


def _metrics(trades: pd.DataFrame, initial: float) -> dict:
    if trades.empty:
        return {"entry_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "initial_equity_krw": initial, "final_equity_krw": initial, "equity_return_pct": 0.0, "total_pnl_krw": 0.0, "max_drawdown_pct": 0.0, "consecutive_loss_max": 0}
    gross_profit = float(trades.loc[trades["trade_pnl_krw"] > 0, "trade_pnl_krw"].sum())
    gross_loss = abs(float(trades.loc[trades["trade_pnl_krw"] < 0, "trade_pnl_krw"].sum()))
    final = float(trades.iloc[-1]["equity_after_trade"])
    losses = trades["trade_pnl_krw"] < 0
    streak = 0
    max_streak = 0
    for value in losses:
        streak = streak + 1 if value else 0
        max_streak = max(max_streak, streak)
    return {"entry_count": int(len(trades)), "win_rate": float((trades["trade_pnl_krw"] > 0).mean()), "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0), "initial_equity_krw": initial, "final_equity_krw": final, "equity_return_pct": (final - initial) / initial * 100 if initial else 0.0, "total_pnl_krw": final - initial, "max_drawdown_pct": float(trades["max_drawdown_pct"].min()) if "max_drawdown_pct" in trades else 0.0, "consecutive_loss_max": max_streak, "avg_allocation_pct": float(trades["allocation_pct"].mean()), "a_plus_trade_count": int((trades["signal_grade"] == "A_PLUS").sum()), "runner_contribution_krw": 0.0, "target_space_capture_ratio": float((trades["realized_pnl_pct"] / trades["target_space_pct"].replace(0, 1)).mean()), "zone_target_hit_rate": float((trades["realized_pnl_pct"] > 0).mean()), "stop_loss_count": int((trades["exit_reason"] == "stop_loss").sum()), "trailing_stop_count": int(trades["trailing_enabled"].sum()), "partial_exit_count": int((trades["exit_plan"] != "FULL_EXIT").sum())}


def _signal_grade(v5_score: float, target_grade: str) -> str:
    if target_grade == "A_PLUS" and v5_score >= 85:
        return "A_PLUS"
    if target_grade in {"A_PLUS", "A"} and v5_score >= 78:
        return "A"
    if target_grade in {"A_PLUS", "A", "B"} and v5_score >= 70:
        return "B"
    if target_grade == "C":
        return "C"
    return "REJECT"
