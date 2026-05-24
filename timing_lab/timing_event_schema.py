from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


EVENT_TYPES = [
    "VOLUME_SPIKE",
    "ORDERFLOW_SHIFT",
    "SPREAD_CONTRACTION",
    "DEPTH_RECOVERY",
    "RANGE_TOUCH",
    "BREAKOUT_PRESSURE",
    "BTC_SHOCK",
    "MARKET_RANK_SURGE",
]


@dataclass(frozen=True)
class TimingEvent:
    event_id: str
    market: str
    event_type: str
    event_time_ms: int
    reference_price: float
    evidence: dict[str, Any] = field(default_factory=dict)
    severity: str = "LOW"
    data_source: str = "UPBIT_WS"
    real_order_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["real_order_enabled"] = False
        return row


def make_event_id(market: str, event_type: str, event_time_ms: int) -> str:
    return f"{market.replace('-', '')}_{event_type}_{event_time_ms}"
