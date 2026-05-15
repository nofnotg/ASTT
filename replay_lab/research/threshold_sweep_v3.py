from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import calc_trade_pnl, summarize_trades


FINAL_SCORE_GRID = [70, 74, 78, 82]
SETUP_SCORE_GRID = [65, 70, 75, 80]
TRIGGER_SCORE_GRID = [65, 70, 75, 80]
CONFIDENCE_GRID = [50, 60, 70]


@dataclass(frozen=True)
class ThresholdConfigV3:
    final_score: float
    setup_score: float
    trigger_score: float
    confidence: float


def generate_threshold_configs() -> list[ThresholdConfigV3]:
    return [
        ThresholdConfigV3(final, setup, trigger, confidence)
        for final, setup, trigger, confidence in itertools.product(FINAL_SCORE_GRID, SETUP_SCORE_GRID, TRIGGER_SCORE_GRID, CONFIDENCE_GRID)
    ]


def run_threshold_sweep_v3(
    start_date: date,
    end_date: date,
    capital_krw: float = 500000,
    order_krw: float = 10000,
    top_markets: int = 50,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "small_seed_v3"
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = build_v3_candidate_outcomes(start_date, end_date, capital_krw, order_krw, top_markets, store_dir)
    rows = evaluate_threshold_configs(candidates, generate_threshold_configs(), capital_krw)
    best = select_best_threshold(rows)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "candidate_rows": int(len(candidates)),
        "best": best,
        "rows": rows,
    }
    if not candidates.empty:
        candidates.to_parquet(out_dir / "threshold_candidate_outcomes.parquet", index=False)
    (out_dir / "threshold_sweep_v3.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_parquet(out_dir / "threshold_sweep_v3.parquet", index=False)
    return out_dir


def build_v3_candidate_outcomes(
    start_date: date,
    end_date: date,
    capital_krw: float,
    order_krw: float,
    top_markets: int = 50,
    store_dir: Path = REPLAY_STORE_DIR,
) -> pd.DataFrame:
    frames = _load_latest_v2_frames(start_date, end_date, store_dir)
    decisions = frames["decisions"]
    personas = frames["personas"]
    if decisions.empty:
        return pd.DataFrame()
    decisions = decisions[decisions["market"].astype(str) != ""].copy()
    if "final_score" not in decisions:
        decisions["final_score"] = 0.0
    if "entry_gate_confidence" not in decisions:
        decisions["entry_gate_confidence"] = 0.0

    pivot = _persona_pivot(personas)
    if not pivot.empty:
        decisions = decisions.merge(pivot, on=["session_id", "date_kst", "market"], how="left")
    for column in ["setup_score", "trigger_score", "risk_score"]:
        if column not in decisions:
            decisions[column] = 0.0
    if "risk_decision" not in decisions:
        decisions["risk_decision"] = "PASS"
    if top_markets:
        ranked = _rank_markets(decisions)
        allowed = set(ranked[:top_markets])
        decisions = decisions[decisions["market"].isin(allowed)].copy()

    cache: dict[str, pd.DataFrame] = {}
    outcomes = []
    for _, row in decisions.iterrows():
        outcome = _simulate_row_outcome(row, cache, store_dir)
        if not outcome.get("entered"):
            continue
        pnl = calc_trade_pnl(capital_krw, order_krw, outcome["signal_pnl_pct"], fee_pct=0.0, slippage_pct=0.0)
        outcomes.append(
            {
                **{key: row.get(key) for key in decisions.columns},
                "entered": True,
                "gross_signal_pnl_pct": pnl["gross_signal_pnl_pct"],
                "net_signal_pnl_pct": pnl["net_signal_pnl_pct"],
                "order_pnl_krw": pnl["order_pnl_krw"],
                "account_pnl_pct": pnl["account_pnl_pct"],
                "exit_reason": outcome["exit_reason"],
                "entry_price": outcome["entry_price"],
                "exit_price": outcome["exit_price"],
            }
        )
    return pd.DataFrame(outcomes)


def evaluate_threshold_configs(candidates: pd.DataFrame, configs: list[ThresholdConfigV3], capital_krw: float = 500000) -> list[dict]:
    rows = []
    total_days = int(candidates["date_kst"].nunique()) if not candidates.empty and "date_kst" in candidates else 0
    for config in configs:
        selected = _select_entries(candidates, config)
        summary = summarize_trades(selected.to_dict("records"), capital_krw)
        rows.append(
            {
                **asdict(config),
                "entry_count": summary["entry_count"],
                "entry_days": summary["entry_days"],
                "hold_days": max(0, total_days - summary["entry_days"]),
                "win_rate": summary["win_rate"],
                "avg_signal_pnl_pct": summary["avg_signal_pnl_pct"],
                "avg_order_pnl_krw": summary["avg_order_pnl_krw"],
                "total_order_pnl_krw": summary["total_order_pnl_krw"],
                "account_return_pct": summary["account_return_pct"],
                "max_drawdown_pct": summary["max_drawdown_pct"],
                "profit_factor": summary["profit_factor"],
                "avg_win_pct": summary["avg_win_pct"],
                "avg_loss_pct": summary["avg_loss_pct"],
                "loss_day_count": summary["loss_day_count"],
                "consecutive_loss_max": summary["consecutive_loss_max"],
                "valid_candidate": _is_valid(summary),
            }
        )
    return sorted(rows, key=lambda row: (row["valid_candidate"], row["account_return_pct"], row["profit_factor"], row["entry_count"]), reverse=True)


def select_best_threshold(rows: list[dict]) -> dict:
    valid = [row for row in rows if row.get("valid_candidate")]
    if not valid:
        return {"status": "NO_VALID_THRESHOLD"}
    best = max(valid, key=lambda row: (row["account_return_pct"], row["profit_factor"], row["entry_count"]))
    return {"status": "VALID_THRESHOLD", **best}


def filter_candidates_by_threshold(candidates: pd.DataFrame, config: dict | ThresholdConfigV3) -> pd.DataFrame:
    if isinstance(config, dict):
        config = ThresholdConfigV3(
            float(config.get("final_score", 82)),
            float(config.get("setup_score", 80)),
            float(config.get("trigger_score", 80)),
            float(config.get("confidence", 70)),
        )
    return _select_entries(candidates, config)


def _select_entries(candidates: pd.DataFrame, config: ThresholdConfigV3) -> pd.DataFrame:
    if candidates.empty:
        return candidates.copy()
    scoped = candidates[
        (candidates["final_score"].astype(float) >= config.final_score)
        & (candidates["setup_score"].astype(float) >= config.setup_score)
        & (candidates["trigger_score"].astype(float) >= config.trigger_score)
        & (candidates["entry_gate_confidence"].astype(float) >= config.confidence)
        & (candidates["risk_decision"].fillna("PASS").astype(str) != "VETO")
    ].copy()
    if scoped.empty:
        return scoped
    scoped = scoped.sort_values(["date_kst", "entry_gate_confidence", "final_score", "market"], ascending=[True, False, False, True])
    return scoped.groupby("date_kst", as_index=False).head(1).copy()


def _is_valid(summary: dict) -> bool:
    return (
        summary["entry_count"] >= 30
        and summary["account_return_pct"] > 0
        and summary["max_drawdown_pct"] >= -8.0
        and summary["profit_factor"] >= 1.1
        and summary["consecutive_loss_max"] <= 3
    )


def _load_latest_v2_frames(start_date: date, end_date: date, store_dir: Path) -> dict[str, pd.DataFrame]:
    experiments = sorted((store_dir / "experiments").glob("exp_*_v2")) if (store_dir / "experiments").exists() else []
    decisions_list = []
    personas_list = []
    for exp in experiments:
        config_path = exp / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        if config.get("mode") != "PAPER_REPLAY_V2":
            continue
        decisions_path = exp / "decisions.parquet"
        personas_path = exp / "persona_scores.parquet"
        if decisions_path.exists():
            frame = pd.read_parquet(decisions_path)
            frame["experiment_id"] = exp.name
            decisions_list.append(frame)
        if personas_path.exists():
            frame = pd.read_parquet(personas_path)
            frame["experiment_id"] = exp.name
            personas_list.append(frame)
    decisions = pd.concat(decisions_list, ignore_index=True) if decisions_list else pd.DataFrame()
    personas = pd.concat(personas_list, ignore_index=True) if personas_list else pd.DataFrame()
    if decisions.empty:
        return {"decisions": decisions, "personas": personas}
    decisions = decisions[(pd.to_datetime(decisions["date_kst"]) >= pd.Timestamp(start_date)) & (pd.to_datetime(decisions["date_kst"]) <= pd.Timestamp(end_date))].copy()
    latest_by_date = decisions.groupby("date_kst")["experiment_id"].max().to_dict()
    decisions = decisions[decisions.apply(lambda row: row["experiment_id"] == latest_by_date.get(row["date_kst"]), axis=1)].copy()
    session_ids = set(decisions["session_id"].astype(str))
    if not personas.empty:
        personas = personas[personas["session_id"].astype(str).isin(session_ids)].copy()
    return {"decisions": decisions, "personas": personas}


def _persona_pivot(personas: pd.DataFrame) -> pd.DataFrame:
    if personas.empty:
        return pd.DataFrame()
    frame = personas.copy()
    frame["persona"] = frame["persona"].astype(str)
    pivot = frame.pivot_table(index=["session_id", "date_kst", "market"], columns="persona", values="score", aggfunc="max").reset_index()
    decisions = frame.pivot_table(index=["session_id", "date_kst", "market"], columns="persona", values="decision", aggfunc="first").reset_index()
    out = pivot[["session_id", "date_kst", "market"]].copy()
    out["setup_score"] = pivot.get("Maggie", pivot.get("매기", pd.Series(0.0, index=pivot.index))).fillna(0.0)
    out["trigger_score"] = pivot.get("Rezo", pd.Series(0.0, index=pivot.index)).fillna(0.0)
    out["risk_score"] = pivot.get("Iris", pd.Series(0.0, index=pivot.index)).fillna(0.0)
    out = out.merge(decisions[["session_id", "date_kst", "market"]].copy(), on=["session_id", "date_kst", "market"], how="left")
    risk = frame[frame["persona"] == "Iris"][["session_id", "date_kst", "market", "decision"]].rename(columns={"decision": "risk_decision"})
    out = out.merge(risk, on=["session_id", "date_kst", "market"], how="left")
    out["risk_decision"] = out["risk_decision"].fillna("PASS")
    return out


def _simulate_row_outcome(row: pd.Series, cache: dict[str, pd.DataFrame], store_dir: Path) -> dict[str, Any]:
    market = str(row.get("market", ""))
    if market not in cache:
        path = store_dir / "normalized" / "candles_1m" / f"{market}.parquet"
        if path.exists():
            frame = pd.read_parquet(path)
            frame["candle_time_kst"] = pd.to_datetime(frame["candle_time_kst"])
            cache[market] = frame.sort_values("candle_time_kst")
        else:
            cache[market] = pd.DataFrame()
    frame = cache[market]
    if frame.empty:
        return {"entered": False, "exit_reason": "no_outcome_data"}
    entry_time = pd.Timestamp(row.get("entry_time_kst") or f"{row['date_kst']}T09:00:00")
    trade_end = pd.Timestamp(row.get("trade_end_time_kst") or f"{row['date_kst']}T10:00:00")
    candles = frame[(frame["candle_time_kst"] >= entry_time) & (frame["candle_time_kst"] <= trade_end)].copy()
    if candles.empty:
        return {"entered": False, "exit_reason": "no_outcome_data"}
    candles = candles.rename(columns={"candle_time_kst": "time"})
    signal_price = float(candles.iloc[0]["open"])
    fill = simulate_long_trade(candles, signal_price, signal_price * 0.985, signal_price * 1.015, fee_pct=0.0, slippage_pct=0.0)
    return {
        "entered": fill.entered,
        "signal_pnl_pct": float(fill.pnl_pct),
        "exit_reason": fill.exit_reason,
        "entry_price": fill.entry_price,
        "exit_price": fill.exit_price,
    }


def _rank_markets(decisions: pd.DataFrame) -> list[str]:
    if "morning_liquidity_score" not in decisions:
        return sorted(decisions["market"].dropna().astype(str).unique())
    rank = decisions.groupby("market")["morning_liquidity_score"].mean().sort_values(ascending=False)
    return [str(item) for item in rank.index]
