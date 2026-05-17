from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from features.edge_isolation import STRATEGY_IDS, build_edge_signal
from features.simple_exit_models import EXIT_MODELS, simulate_simple_exit
from features.trade_review_exporter import build_trade_review_rows
from features.zone_quality_v54 import compute_zone_quality_v54
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment
from replay_lab.replay.structure_reversal_v5 import _load_base_frame


def run_edge_isolation_v54(
    start_date: date,
    end_date: date,
    top_markets: int = 50,
    fixed_order_krw: float = 10000,
    strategy_ids: list[str] | None = None,
    exit_models: list[str] | None = None,
    use_btc_regime: bool = True,
    use_zone_quality_v54: bool = True,
    replay_mode: str = "walk_forward_day_by_day",
    config: dict | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    strategy_ids = strategy_ids or STRATEGY_IDS
    exit_models = exit_models or ["FIXED_RR_1_0", "FIXED_RR_1_2", "FIXED_RR_1_5", "ZONE_TARGET_FULL_EXIT", "TP1_BREAK_EVEN"]
    exp_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_edge_isolation_v54")
    exp_dir = store_dir / "experiments" / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    seed, seed_meta = _load_seed(start_date, end_date, store_dir)
    trades = _build_trades(seed, strategy_ids, exit_models, fixed_order_krw, store_dir, use_zone_quality_v54)
    strategy_results = [_summarize(trades[trades["strategy_id"] == sid], fixed_order_krw, {"strategy_id": sid}) for sid in strategy_ids]
    exit_results = [_summarize(trades[trades["exit_model"] == model], fixed_order_krw, {"exit_model": model}) for model in exit_models]
    ablation = _ablation(trades, fixed_order_krw)
    review_rows = build_trade_review_rows(_best_review_frame(trades))
    best = max(strategy_results, key=lambda row: (row["profit_factor"], row["entry_count"])) if strategy_results else {}
    metrics = {
        "schema_version": "1.0",
        "experiment_id": exp_id,
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "top_markets": top_markets,
        "fixed_order_krw": fixed_order_krw,
        "seed_source": seed_meta,
        "full_validation_completed": _full_coverage(seed_meta, start_date, end_date, top_markets),
        "strategy_results": strategy_results,
        "exit_model_results": exit_results,
        "module_ablation_results": ablation,
        "best_simple_strategy": best,
        "trade_review_count": len(review_rows),
        "live_readiness": _readiness(best, seed_meta, start_date, end_date, top_markets),
    }
    trades.to_parquet(exp_dir / "edge_trades.parquet", index=False)
    pd.DataFrame(review_rows).to_parquet(exp_dir / "trade_review.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "config.json").write_text(json.dumps({"experiment_id": exp_id, "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "strategy_ids": strategy_ids, "exit_models": exit_models, "fixed_order_krw": fixed_order_krw, "use_btc_regime": use_btc_regime, "use_zone_quality_v54": use_zone_quality_v54, "replay_mode": replay_mode, "config": config or {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def latest_edge_isolation_v54_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    exps = sorted((store_dir / "experiments").glob("exp_*_edge_isolation_v54"), key=lambda p: p.name)
    return exps[-1] if exps else None


def _load_seed(start_date: date, end_date: date, store_dir: Path) -> tuple[pd.DataFrame, dict]:
    exp = latest_fractal_v53_experiment(store_dir)
    if exp and (exp / "paper_trades.parquet").exists():
        trades = pd.read_parquet(exp / "paper_trades.parquet")
        cfg = json.loads((exp / "config.json").read_text(encoding="utf-8")) if (exp / "config.json").exists() else {}
        mask = (pd.to_datetime(trades["date_kst"]).dt.date >= start_date) & (pd.to_datetime(trades["date_kst"]).dt.date <= end_date)
        return trades[mask].copy(), {"experiment": exp.name, **cfg}
    return pd.DataFrame(), {"experiment": None, "empty_seed": True}


def _build_trades(seed: pd.DataFrame, strategy_ids: list[str], exit_models: list[str], fixed_order_krw: float, store_dir: Path, use_zone_quality: bool) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for trade in seed.to_dict("records"):
        base = _load_base_frame(store_dir, trade["market"])
        entry_time = pd.Timestamp(trade["entry_time_kst"])
        post = base[(base["time"] > entry_time) & (base["time"] <= entry_time + pd.Timedelta(minutes=180))].copy()
        for sid in strategy_ids:
            signal = build_edge_signal(trade, sid)
            if not signal["entry_allowed"]:
                continue
            zone_quality = _zone_quality(trade, base, use_zone_quality)
            for model in exit_models:
                exit_row = simulate_simple_exit(post, signal["entry_price"], signal["stop_price"], model, {"target_1": trade.get("target_1", signal["entry_price"] * 1.01)})
                pnl_krw = fixed_order_krw * exit_row["realized_pnl_pct"] / 100
                rows.append(
                    {
                        **trade,
                        **exit_row,
                        "strategy_id": sid,
                        "strategy_score": signal["strategy_score"],
                        "stop_price": signal["stop_price"],
                        "target_price": trade.get("target_1", 0.0),
                        "target_space_pct": trade.get("target_space_pct", (float(trade.get("target_1", signal["entry_price"])) - signal["entry_price"]) / signal["entry_price"] * 100 if signal["entry_price"] else 0.0),
                        "order_pnl_krw": pnl_krw,
                        "zone_used": sid in {"ZONE_ONLY", "MTF_PLUS_ZONE"},
                        "zone_low": trade.get("zone_stop", 0.0),
                        "zone_high": trade.get("entry_price", 0.0),
                        "zone_quality_score": zone_quality["zone_quality_score"],
                        "zone_quality_grade": zone_quality["quality_grade"],
                        "entry_reason": ";".join(signal["setup_reasons"]),
                        "invalid_reason": "",
                    }
                )
    return pd.DataFrame(rows)


def _zone_quality(trade: dict, base: pd.DataFrame, enabled: bool) -> dict:
    if not enabled:
        return {"zone_quality_score": 0.0, "quality_grade": "DISABLED"}
    as_of = trade.get("signal_time_kst", trade.get("entry_time_kst"))
    zone = {"zone_low": trade.get("zone_stop", 0.0), "zone_high": trade.get("entry_price", 0.0)}
    return compute_zone_quality_v54(zone, base.tail(300), as_of_time=as_of)


def _summarize(trades: pd.DataFrame, fixed_order_krw: float, extra: dict) -> dict:
    if trades.empty:
        return {**extra, "entry_count": 0, "win_rate": 0.0, "avg_win_pct": 0.0, "avg_loss_pct": 0.0, "profit_factor": 0.0, "expectancy_pct": 0.0, "max_drawdown_pct": 0.0, "consecutive_loss_max": 0, "time_stop_count": 0, "stop_loss_count": 0, "take_profit_count": 0}
    pnl = trades["realized_pnl_pct"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gp = float((wins / 100 * fixed_order_krw).sum())
    gl = abs(float((losses / 100 * fixed_order_krw).sum()))
    equity = fixed_order_krw * 50
    peak = equity
    mdd = 0.0
    streak = 0
    max_streak = 0
    for value in pnl:
        equity += fixed_order_krw * value / 100
        peak = max(peak, equity)
        mdd = min(mdd, (equity - peak) / peak * 100 if peak else 0.0)
        streak = streak + 1 if value < 0 else 0
        max_streak = max(max_streak, streak)
    return {**extra, "entry_count": int(len(trades)), "win_rate": float((pnl > 0).mean()), "avg_win_pct": float(wins.mean()) if len(wins) else 0.0, "avg_loss_pct": float(losses.mean()) if len(losses) else 0.0, "profit_factor": gp / gl if gl else (999.0 if gp else 0.0), "expectancy_pct": float(pnl.mean()), "max_drawdown_pct": mdd, "consecutive_loss_max": max_streak, "time_stop_count": int((trades["exit_reason"] == "TIME_STOP").sum()), "stop_loss_count": int((trades["exit_reason"] == "STOP_LOSS").sum()), "take_profit_count": int((trades["exit_reason"] == "TAKE_PROFIT").sum())}


def _ablation(trades: pd.DataFrame, fixed_order_krw: float) -> list[dict]:
    mapping = {
        "BASE_TRIGGER_ONLY": trades,
        "BASE+DAILY": trades[trades["daily_structure_score"].astype(float) >= 55] if not trades.empty else trades,
        "BASE+H4": trades[trades["h4_flow_score"].astype(float) >= 50] if not trades.empty else trades,
        "BASE+DAILY+H4": trades[(trades["daily_structure_score"].astype(float) >= 55) & (trades["h4_flow_score"].astype(float) >= 50)] if not trades.empty else trades,
        "BASE+ZONE": trades[trades["zone_used"] == True] if not trades.empty else trades,
        "BASE+DAILY+H4+ZONE": trades[(trades["daily_structure_score"].astype(float) >= 55) & (trades["h4_flow_score"].astype(float) >= 50) & (trades["zone_used"] == True)] if not trades.empty else trades,
        "BASE+DAILY+H4+ZONE+BTC": trades[(trades["daily_structure_score"].astype(float) >= 55) & (trades["h4_flow_score"].astype(float) >= 50) & (trades["zone_used"] == True) & (trades["btc_regime"].astype(str) != "RISK_OFF")] if not trades.empty and "btc_regime" in trades else trades,
        "BASE+DAILY+H4+ZONE+TARGET": trades[(trades["daily_structure_score"].astype(float) >= 55) & (trades["h4_flow_score"].astype(float) >= 50) & (trades["zone_used"] == True) & (trades["target_space_pct"].astype(float) >= 1.0)] if not trades.empty else trades,
    }
    return [_summarize(frame, fixed_order_krw, {"module_stack": name}) for name, frame in mapping.items()]


def _best_review_frame(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    return trades.sort_values(["date_kst", "strategy_id", "exit_model"]).groupby(["date_kst", "market"], as_index=False).head(1)


def _full_coverage(seed_meta: dict, start_date: date, end_date: date, top_markets: int) -> bool:
    try:
        return date.fromisoformat(str(seed_meta.get("start_date"))) <= start_date and date.fromisoformat(str(seed_meta.get("end_date"))) >= end_date and int(seed_meta.get("top_markets", 0)) >= top_markets
    except (TypeError, ValueError):
        return False


def _readiness(best: dict, seed_meta: dict, start_date: date, end_date: date, top_markets: int) -> str:
    if not _full_coverage(seed_meta, start_date, end_date, top_markets):
        return "LIVE_NOT_ALLOWED"
    if best.get("entry_count", 0) < 30 or best.get("profit_factor", 0.0) < 1.1 or best.get("expectancy_pct", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    return "PAPER_MORE_REQUIRED"
