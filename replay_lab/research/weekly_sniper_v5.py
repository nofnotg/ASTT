from __future__ import annotations

from datetime import date
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.structure_reversal_v5 import StructureReversalV5Config, run_structure_reversal_v5


def run_weekly_sniper_v5(start_date: date, end_date: date, markets: list[str], top_markets: int = 50, capital_krw: float = 500000, order_krw: float = 10000, store_dir: Path = REPLAY_STORE_DIR) -> Path:
    config = StructureReversalV5Config(
        weekly_min_score=70,
        daily_min_score=75,
        h4_min_score=70,
        v5_min_score=85,
        risk_reward_min=1.5,
        mode="weekly_sniper",
        max_hold_minutes=2880,
    )
    return run_structure_reversal_v5(start_date, end_date, markets, top_markets=top_markets, capital_krw=capital_krw, order_krw=order_krw, mode="weekly_sniper", config=config, store_dir=store_dir)
