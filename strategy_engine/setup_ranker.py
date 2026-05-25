from __future__ import annotations


def rank_setups(setups: list[dict], limit: int = 50) -> list[dict]:
    return sorted(setups, key=lambda row: (row.get("setup_quality_score", 0.0), row.get("risk_reward_ratio", 0.0)), reverse=True)[:limit]
