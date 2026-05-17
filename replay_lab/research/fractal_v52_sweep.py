from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v52 import FractalV52Config, run_fractal_v52, latest_fractal_v52_experiment


def run_fractal_v52_sweep(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v52"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for allocation_model in ["fixed_10k", "grade_based"]:
        for exit_model in ["target_zone_full_exit", "partial_tp_runner"]:
            run_fractal_v52(start_date, end_date, markets, top_markets=top_markets, initial_equity_krw=initial_equity_krw, allocation_model=allocation_model, exit_model=exit_model, store_dir=store_dir)
            exp = latest_fractal_v52_experiment(store_dir)
            metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp else {}
            rows.append({"allocation_model": allocation_model, "exit_model": exit_model, **metrics})
    best = max(rows, key=lambda r: (r.get("profit_factor", 0.0), r.get("equity_return_pct", 0.0), r.get("entry_count", 0))) if rows else {}
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()}, "best": best, "results": rows}
    (out_dir / "fractal_v52_sweep.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_parquet(out_dir / "fractal_v52_sweep.parquet", index=False)
    return out_dir
