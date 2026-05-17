from __future__ import annotations

from datetime import date
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fractal_v53 import run_fractal_v53


def run_fractal_v53_full_validation(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, initial_equity_krw: float = 500000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    return run_fractal_v53(start_date, end_date, markets, top_markets=top_markets, initial_equity_krw=initial_equity_krw, store_dir=store_dir)
