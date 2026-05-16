from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.structure_reversal_v5 import StructureReversalV5Config, scan_structure_reversal_v5
from replay_lab.research.small_seed_metrics import summarize_trades


def run_structure_reversal_sweep_v5(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, capital_krw: float = 500000, order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "structure_reversal_v5"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_config = StructureReversalV5Config(weekly_min_score=0, daily_min_score=0, h4_min_score=0, v5_min_score=0, risk_reward_min=1.0)
    candidates, trades = scan_structure_reversal_v5(start_date, end_date, markets[:top_markets], capital_krw, order_krw, base_config, store_dir)
    candidates.to_parquet(out_dir / "structure_reversal_v5_base_candidates.parquet", index=False)
    trades.to_parquet(out_dir / "structure_reversal_v5_base_trades.parquet", index=False)
    rows = []
    for config in _configs():
        selected = _filter(trades, config)
        if not selected.empty:
            selected = selected.sort_values(["date_kst", "v5_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(1)
        summary = summarize_trades(selected.to_dict("records"), capital_krw)
        rows.append({**summary, "status": _status(summary), **asdict(config)})
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame.to_parquet(out_dir / "structure_reversal_sweep_v5.parquet", index=False)
    best = _best(rows)
    payload: dict[str, Any] = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "capital_krw": capital_krw, "order_krw": order_krw, "candidate_count": int(len(candidates)), "base_entry_count": int(len(trades)), "best": best, "results": rows}
    (out_dir / "structure_reversal_sweep_v5.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir


def _configs() -> list[StructureReversalV5Config]:
    configs = []
    for weekly in [50, 60, 70]:
        for daily in [55, 65, 75]:
            for h4 in [50, 60, 70]:
                for v5 in [70, 75, 80, 85]:
                    for rr in [1.0, 1.2, 1.5]:
                        for ichimoku in [False, True]:
                            configs.append(StructureReversalV5Config(weekly_min_score=weekly, daily_min_score=daily, h4_min_score=h4, v5_min_score=v5, risk_reward_min=rr, use_ichimoku=ichimoku))
    return configs


def _filter(frame: pd.DataFrame, config: StructureReversalV5Config) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    data = frame.copy()
    data = data[data["weekly_bias_score"].astype(float) >= config.weekly_min_score]
    data = data[data["daily_structure_score"].astype(float) >= config.daily_min_score]
    data = data[data["h4_flow_score"].astype(float) >= config.h4_min_score]
    data = data[data["v5_score"].astype(float) >= config.v5_min_score]
    data = data[data["risk_reward"].astype(float) >= config.risk_reward_min]
    if config.use_ichimoku:
        data = data[data["use_ichimoku"].astype(bool)]
    return data


def _status(summary: dict) -> str:
    if summary.get("entry_count", 0) < 30:
        return "V5_INSUFFICIENT_SAMPLE"
    if summary.get("account_return_pct", 0.0) > 0 and summary.get("profit_factor", 0.0) >= 1.1 and summary.get("consecutive_loss_max", 0) <= 3:
        return "V5_VALID"
    if summary.get("account_return_pct", 0.0) <= 0 or summary.get("profit_factor", 0.0) < 0.9:
        return "V5_REJECTED"
    return "PAPER_MORE_REQUIRED"


def _best(rows: list[dict]) -> dict:
    if not rows:
        return {"status": "V5_INSUFFICIENT_SAMPLE"}
    return max(rows, key=lambda row: (row.get("entry_count", 0), row.get("profit_factor", 0.0), row.get("account_return_pct", 0.0), row.get("max_drawdown_pct", -999.0)))
