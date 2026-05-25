from __future__ import annotations

from strategy_engine.setup_ranker import rank_setups


def rank_candidates(candidates: list[dict], limit: int = 50) -> list[dict]:
    return rank_setups(candidates, limit)
