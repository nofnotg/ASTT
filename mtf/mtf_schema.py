from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class MTFContext:
    market: str
    weekly_trend: str
    daily_trend: str
    h4_structure: str
    h1_setup_bias: str
    mtf_score: float
    risk_regime: str

    def to_dict(self) -> dict:
        return asdict(self)
