from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v52 import latest_fractal_v52_experiment, run_fractal_v52


def compare_full_seed_v52(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v52"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in ["fixed_10k", "full_seed", "grade_based"]:
        run_fractal_v52(start_date, end_date, markets, top_markets=top_markets, initial_equity_krw=initial_equity_krw, allocation_model=model, store_dir=store_dir)
        exp = latest_fractal_v52_experiment(store_dir)
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp else {}
        rows.append({"allocation_model": model, **metrics})
    best = max(rows, key=lambda r: (r.get("final_equity_krw", 0.0), r.get("profit_factor", 0.0))) if rows else {}
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "results": rows, "best_allocation_model": best.get("allocation_model", "")}
    (out_dir / "full_seed_compounding_compare_v52.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
