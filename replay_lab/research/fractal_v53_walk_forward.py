from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import latest_fractal_v53_experiment, run_fractal_v53


def run_fractal_v53_walk_forward(start_date: date, end_date: date, markets: list[str] | None = None, top_markets: int = 50, initial_equity_krw: float = 500000, use_cache: bool = True, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v53"
    out_dir.mkdir(parents=True, exist_ok=True)
    windows = []
    cursor = start_date
    while cursor + timedelta(days=44) <= end_date:
        train_start = cursor
        train_end = cursor + timedelta(days=30)
        test_start = train_end + timedelta(days=1)
        test_end = min(test_start + timedelta(days=14), end_date)
        run_fractal_v53(test_start, test_end, markets or [], top_markets=top_markets, initial_equity_krw=initial_equity_krw, use_cache=use_cache, store_dir=store_dir)
        exp = latest_fractal_v53_experiment(store_dir)
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp else {}
        windows.append({"train_start": train_start.isoformat(), "train_end": train_end.isoformat(), "test_start": test_start.isoformat(), "test_end": test_end.isoformat(), **metrics})
        cursor += timedelta(days=15)
    avg_pf = sum(w.get("profit_factor", 0.0) for w in windows) / len(windows) if windows else 0.0
    median_pf = float(pd.Series([w.get("profit_factor", 0.0) for w in windows]).median()) if windows else 0.0
    positive_ratio = sum(1 for w in windows if w.get("equity_return_pct", 0.0) > 0) / len(windows) if windows else 0.0
    avg_return = sum(w.get("equity_return_pct", 0.0) for w in windows) / len(windows) if windows else 0.0
    worst_mdd = min((w.get("max_drawdown_pct", 0.0) for w in windows), default=0.0)
    stable = bool(len(windows) >= 3 and positive_ratio >= 0.6 and avg_pf >= 1.1 and worst_mdd >= -8)
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "window_count": len(windows), "windows": windows, "avg_test_profit_factor": avg_pf, "median_test_profit_factor": median_pf, "positive_window_ratio": positive_ratio, "avg_test_return_pct": avg_return, "worst_window_mdd_pct": worst_mdd, "stable": stable, "overfitting_warning": [] if stable else ["walk_forward_not_stable"]}
    (out_dir / "fractal_v53_walk_forward.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
