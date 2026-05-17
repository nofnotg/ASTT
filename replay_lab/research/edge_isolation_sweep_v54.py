from __future__ import annotations

from datetime import date
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import run_edge_isolation_v54


def run_edge_isolation_sweep_v54(start_date: date, end_date: date, top_markets: int = 50, fixed_order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    return run_edge_isolation_v54(start_date, end_date, top_markets=top_markets, fixed_order_krw=fixed_order_krw, store_dir=store_dir)
