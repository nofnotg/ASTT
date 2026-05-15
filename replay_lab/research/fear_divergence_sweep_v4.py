from __future__ import annotations

import itertools
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_divergence_v4 import FearDivergenceConfig, scan_fear_divergence_v4
from replay_lab.research.small_seed_metrics import summarize_trades


@dataclass(frozen=True)
class FearDivergenceSweepConfig:
    timeframe: str = "5m"
    lookback: int = 30
    bollinger_length: int = 30
    bollinger_stddev: float = 2.0
    min_divergence_strength: float = 60.0
    min_v4_score: float = 70.0
    min_body_zone_score: float = 40.0
    min_trendline_score: float = 40.0
    exit_mode: str = "middle_band"


def generate_sweep_configs(timeframe: str = "5m") -> list[FearDivergenceSweepConfig]:
    return [
        FearDivergenceSweepConfig(timeframe, lookback, 30, stddev, div, score, body, trend, exit_mode)
        for lookback, stddev, div, score, body, trend, exit_mode in itertools.product(
            [20, 30, 50],
            [2.0, 2.5],
            [60, 70, 80],
            [70, 75, 80],
            [30, 40, 50],
            [30, 40, 50],
            ["middle_band", "ma30", "fixed_rr"],
        )
    ]


def run_fear_divergence_sweep_v4(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    timeframe: str = "5m",
    top_markets: int = 50,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "fear_divergence_v4"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_config = FearDivergenceConfig(timeframe=timeframe, lookback=50, bollinger_stddev=2.5, min_divergence_strength=45, min_v4_score=45, min_body_zone_score=20, min_trendline_score=20)
    candidates, trades = scan_fear_divergence_v4(start_date, end_date, markets[:top_markets], capital_krw, order_krw, base_config, store_dir)
    rows = evaluate_sweep_results(trades, generate_sweep_configs(timeframe), capital_krw)
    best = select_best_config(rows)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "timeframe": timeframe,
        "candidate_count": int(len(candidates)),
        "base_trade_count": int(len(trades)),
        "best": best,
        "rows": rows,
    }
    candidates.to_parquet(out_dir / "fear_divergence_candidates_v4.parquet", index=False)
    trades.to_parquet(out_dir / "fear_divergence_base_trades_v4.parquet", index=False)
    pd.DataFrame(rows).to_parquet(out_dir / "fear_divergence_sweep_v4.parquet", index=False)
    (out_dir / "fear_divergence_sweep_v4.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def evaluate_sweep_results(trades: pd.DataFrame, configs: list[FearDivergenceSweepConfig], capital_krw: float = 500000) -> list[dict]:
    rows = []
    for config in configs:
        selected = _filter_trades(trades, config)
        summary = summarize_trades(selected.to_dict("records"), capital_krw)
        reject_count = 0 if trades.empty else int(len(trades) - len(selected))
        rows.append(
            {
                **asdict(config),
                "entry_count": summary["entry_count"],
                "win_rate": summary["win_rate"],
                "avg_signal_pnl_pct": summary["avg_signal_pnl_pct"],
                "avg_order_pnl_krw": summary["avg_order_pnl_krw"],
                "total_order_pnl_krw": summary["total_order_pnl_krw"],
                "account_return_pct": summary["account_return_pct"],
                "max_drawdown_pct": summary["max_drawdown_pct"],
                "profit_factor": summary["profit_factor"],
                "consecutive_loss_max": summary["consecutive_loss_max"],
                "avg_hold_minutes": float(selected["hold_minutes"].mean()) if not selected.empty and "hold_minutes" in selected else 0.0,
                "skeptic_reject_count": reject_count,
                "skeptic_saved_loss_estimate": _saved_loss_estimate(trades, selected),
                "valid_candidate": _is_valid(summary),
            }
        )
    return sorted(rows, key=lambda row: (row["valid_candidate"], row["account_return_pct"], row["profit_factor"], row["entry_count"]), reverse=True)


def select_best_config(rows: list[dict]) -> dict:
    valid = [row for row in rows if row.get("valid_candidate")]
    if not valid:
        return {"status": "NO_VALID_FEAR_DIVERGENCE_CONFIG"}
    best = max(valid, key=lambda row: (row["account_return_pct"], row["profit_factor"], row["entry_count"]))
    return {"status": "VALID_FEAR_DIVERGENCE_CONFIG", **best}


def _filter_trades(trades: pd.DataFrame, config: FearDivergenceSweepConfig) -> pd.DataFrame:
    if trades.empty:
        return trades.copy()
    scoped = trades[
        (trades["divergence_strength"].astype(float) >= config.min_divergence_strength)
        & (trades["v4_score"].astype(float) >= config.min_v4_score)
        & (
            (trades["body_zone_score"].astype(float) >= config.min_body_zone_score)
            | (trades["trendline_score"].astype(float) >= config.min_trendline_score)
        )
    ].copy()
    if scoped.empty:
        return scoped
    return scoped.sort_values(["date_kst", "v4_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(1)


def _is_valid(summary: dict) -> bool:
    return (
        summary["entry_count"] >= 30
        and summary["win_rate"] >= 0.50
        and summary["profit_factor"] >= 1.2
        and summary["account_return_pct"] > 0
        and summary["max_drawdown_pct"] >= -8.0
        and summary["consecutive_loss_max"] <= 3
    )


def _saved_loss_estimate(all_trades: pd.DataFrame, selected: pd.DataFrame) -> float:
    if all_trades.empty:
        return 0.0
    selected_ids = set(selected.get("signal_time_kst", pd.Series(dtype=str)).astype(str) + "|" + selected.get("market", pd.Series(dtype=str)).astype(str)) if not selected.empty else set()
    all_ids = all_trades["signal_time_kst"].astype(str) + "|" + all_trades["market"].astype(str)
    rejected = all_trades[~all_ids.isin(selected_ids)]
    return abs(float(rejected.loc[rejected["order_pnl_krw"].astype(float) < 0, "order_pnl_krw"].sum())) if not rejected.empty else 0.0
