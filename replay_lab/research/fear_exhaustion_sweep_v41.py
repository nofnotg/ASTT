from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_exhaustion_v41 import FearExhaustionV41Config, scan_fear_exhaustion_v41
from replay_lab.research.small_seed_metrics import summarize_trades


def run_fear_exhaustion_sweep_v41(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    timeframes: list[str] | None = None,
    top_markets: int = 50,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    """Build a relaxed base sample, then test threshold profiles against it."""
    timeframes = timeframes or ["1m", "5m"]
    out_dir = store_dir / "reports" / "fear_exhaustion_v41"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    base_funnels: dict[str, dict] = {}
    base_candidate_counts: dict[str, int] = {}
    for timeframe in timeframes:
        base_config = _base_config(timeframe)
        candidates, trades, funnel = scan_fear_exhaustion_v41(start_date, end_date, markets[:top_markets], capital_krw, order_krw, base_config, store_dir)
        base_funnels[timeframe] = funnel
        base_candidate_counts[timeframe] = int(len(candidates))
        candidates.to_parquet(out_dir / f"fear_exhaustion_v41_base_candidates_{timeframe}.parquet", index=False)
        trades.to_parquet(out_dir / f"fear_exhaustion_v41_base_trades_{timeframe}.parquet", index=False)
        if candidates.empty or trades.empty:
            rows.append(_empty_result(timeframe, base_config, funnel))
            continue
        merged = trades.merge(
            candidates[
                [
                    "market",
                    "signal_time_kst",
                    "drop_pct",
                    "low_structure_score",
                    "cooling_score",
                    "reentry_strength",
                    "support_context_score",
                    "target_space_pct",
                    "v41_score",
                    "would_block",
                ]
            ],
            on=["market", "signal_time_kst"],
            how="left",
            suffixes=("", "_candidate"),
        )
        for config in _threshold_configs(timeframe):
            selected = _filter_by_config(merged, config)
            selected = selected.sort_values(["date_kst", "signal_time_kst", "v41_score"], ascending=[True, True, False]).groupby("date_kst", as_index=False).head(1)
            summary = summarize_trades(selected.to_dict("records"), capital_krw)
            rows.append(
                {
                    **summary,
                    "status": _status(summary),
                    "timeframe": timeframe,
                    "candidate_count": int(len(candidates)),
                    "selected_candidate_count": int(len(selected)),
                    "skeptic_would_block_count": int(selected.get("would_block", pd.Series(dtype=bool)).astype(bool).sum()) if not selected.empty else 0,
                    "funnel_stage_counts": funnel,
                    **asdict(config),
                }
            )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_parquet(out_dir / "fear_exhaustion_sweep_v41.parquet", index=False)
    best = _best_result(rows)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "timeframes": timeframes,
        "base_candidate_counts": base_candidate_counts,
        "base_funnels": base_funnels,
        "best": best,
        "results": rows,
    }
    (out_dir / "fear_exhaustion_sweep_v41.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _base_config(timeframe: str) -> FearExhaustionV41Config:
    min_drop = 0.5 if timeframe == "1m" else 0.8
    return FearExhaustionV41Config(
        timeframe=timeframe,
        lookback=24,
        min_drop_pct=min_drop,
        low_tolerance_pct=0.7,
        cooling_ratio=0.95,
        bollinger_length=20,
        bollinger_stddev=2.5,
        min_support_score=0,
        min_v41_score=0,
        exit_mode="middle_band",
        skeptic_guard_mode="DIAGNOSTIC",
        blocking_enabled=False,
    )


def _threshold_configs(timeframe: str) -> list[FearExhaustionV41Config]:
    drop_values = [0.5, 0.7, 1.0] if timeframe == "1m" else [0.8, 1.2, 1.5]
    configs: list[FearExhaustionV41Config] = []
    for min_drop_pct in drop_values:
        for low_tolerance_pct in [0.3, 0.5, 0.7]:
            for cooling_ratio in [0.95, 0.90, 0.85]:
                for min_support_score in [30, 40, 50]:
                    for min_v41_score in [60, 65, 70, 75]:
                        configs.append(
                            FearExhaustionV41Config(
                                timeframe=timeframe,
                                min_drop_pct=min_drop_pct,
                                low_tolerance_pct=low_tolerance_pct,
                                cooling_ratio=cooling_ratio,
                                bollinger_length=20,
                                bollinger_stddev=2.5,
                                min_support_score=float(min_support_score),
                                min_v41_score=float(min_v41_score),
                                exit_mode="middle_band",
                                skeptic_guard_mode="DIAGNOSTIC",
                                blocking_enabled=False,
                            )
                        )
    return configs


def _filter_by_config(frame: pd.DataFrame, config: FearExhaustionV41Config) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    selected = frame.copy()
    selected = selected[selected["drop_pct"].astype(float) >= config.min_drop_pct]
    selected = selected[selected["support_context_score"].astype(float) >= config.min_support_score]
    selected = selected[selected["v41_score"].astype(float) >= config.min_v41_score]
    selected = selected[selected["target_space_pct"].astype(float) >= 0.4]
    return selected


def _status(summary: dict) -> str:
    if summary.get("entry_count", 0) < 30:
        return "NO_VALID_CONFIG"
    if (
        summary.get("profit_factor", 0.0) >= 1.1
        and summary.get("account_return_pct", 0.0) > 0
        and summary.get("consecutive_loss_max", 0) <= 4
        and summary.get("max_drawdown_pct", 0.0) >= -8.0
    ):
        return "STRATEGY_VALID"
    return "SAMPLE_CREATED"


def _best_result(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"status": "NO_VALID_CONFIG"}
    valid = [row for row in rows if row.get("status") == "STRATEGY_VALID"]
    sampled = [row for row in rows if row.get("entry_count", 0) >= 30]
    pool = valid or sampled or rows
    return max(
        pool,
        key=lambda row: (
            row.get("status") == "STRATEGY_VALID",
            row.get("entry_count", 0),
            row.get("profit_factor", 0.0),
            row.get("account_return_pct", 0.0),
            row.get("max_drawdown_pct", -999.0),
        ),
    )


def _empty_result(timeframe: str, config: FearExhaustionV41Config, funnel: dict) -> dict[str, Any]:
    return {
        "status": "NO_VALID_CONFIG",
        "timeframe": timeframe,
        "candidate_count": 0,
        "selected_candidate_count": 0,
        "skeptic_would_block_count": 0,
        "funnel_stage_counts": funnel,
        **asdict(config),
        "entry_count": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "account_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "consecutive_loss_max": 0,
        "total_order_pnl_krw": 0.0,
    }
