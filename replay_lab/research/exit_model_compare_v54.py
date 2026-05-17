from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment, run_edge_isolation_v54


def compare_exit_models_v54(start_date: date, end_date: date, top_markets: int = 50, fixed_order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    out_dir = store_dir / "reports" / "edge_isolation_v54"
    out_dir.mkdir(parents=True, exist_ok=True)
    exp = latest_edge_isolation_v54_experiment(store_dir) or run_edge_isolation_v54(start_date, end_date, top_markets, fixed_order_krw, store_dir=store_dir)
    metrics = json.loads((exp / "metrics.json").read_text(encoding="utf-8"))
    payload = {"schema_version": "1.0", "generated_at": datetime.utcnow().isoformat(), "exit_model_results": metrics.get("exit_model_results", [])}
    (out_dir / "exit_model_compare_v54.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_dir
