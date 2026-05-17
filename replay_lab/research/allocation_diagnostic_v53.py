from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from features.allocation_diagnostic import build_allocation_diagnostic
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment


def diagnose_allocation_v53(start_date: date, end_date: date, top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v53"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_fractal_v53_experiment(store_dir)
    trades = pd.read_parquet(exp / "paper_trades.parquet") if exp and (exp / "paper_trades.parquet").exists() else pd.DataFrame()
    result = build_allocation_diagnostic(trades, initial_equity_krw)
    payload = {k: v for k, v in result.items() if k != "rows"}
    payload.update({"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "top_markets": top_markets})
    (out_dir / "allocation_diagnostic_v53.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
