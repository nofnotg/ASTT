from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class EventClipMeta:
    clip_id: str
    event_id: str
    market: str
    event_type: str
    event_time_ms: int
    clip_start_ms: int
    clip_end_ms: int
    pre_window_seconds: int = 600
    post_window_seconds: int = 1800
    trade_event_count: int = 0
    orderbook_event_count: int = 0
    ticker_event_count: int = 0
    quality: str = "POOR"
    source: str = "RECORDED_REPLAY"
    status: str = "OPEN"
    real_order_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        row = asdict(self)
        row["real_order_enabled"] = False
        return row
