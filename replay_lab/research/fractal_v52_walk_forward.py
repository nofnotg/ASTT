from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v52 import latest_fractal_v52_experiment, run_fractal_v52


def run_fractal_v52_walk_forward(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "fractal_v52"
    out_dir.mkdir(parents=True, exist_ok=True)
    windows = []
    cursor = start_date
    while cursor + timedelta(days=44) <= end_date:
        train_start = cursor
        train_end = cursor + timedelta(days=30)
        test_start = train_end + timedelta(days=1)
        test_end = min(test_start + timedelta(days=14), end_date)
        run_fractal_v52(test_start, test_end, markets, top_markets=top_markets, initial_equity_krw=initial_equity_krw, store_dir=store_dir)
        exp = latest_fractal_v52_experiment(store_dir)
        metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8")) if exp else {}
        windows.append({"train_start": train_start.isoformat(), "train_end": train_end.isoformat(), "test_start": test_start.isoformat(), "test_end": test_end.isoformat(), **metrics})
        cursor += timedelta(days=15)
    avg_pf = sum(w.get("profit_factor", 0.0) for w in windows) / len(windows) if windows else 0.0
    avg_ret = sum(w.get("equity_return_pct", 0.0) for w in windows) / len(windows) if windows else 0.0
    worst_mdd = min((w.get("max_drawdown_pct", 0.0) for w in windows), default=0.0)
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "windows": windows, "avg_test_profit_factor": avg_pf, "avg_test_return_pct": avg_ret, "worst_window_mdd_pct": worst_mdd, "stable": bool(windows and avg_pf >= 1.1 and worst_mdd >= -8), "overfitting_warning": [] if windows else ["no_walk_forward_windows"]}
    (out_dir / "fractal_v52_walk_forward.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
