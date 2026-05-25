from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class StrategySetup:
    market: str
    strategy: str
    setup_type: str
    setup_quality_score: float
    entry_price: float
    stop_price: float
    target_price: float
    risk_reward_ratio: float
    evidence: dict

    def to_dict(self) -> dict:
        return asdict(self)
