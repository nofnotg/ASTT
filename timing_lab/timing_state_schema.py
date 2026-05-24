from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


STATES = ["IDLE", "WATCH", "ARMED", "TRIGGERED", "CONFIRMED", "ENTER", "ABORT"]


@dataclass(frozen=True)
class TimingStateSnapshot:
    market: str
    event_id: str
    state: str
    state_entered_at_ms: int
    state_age_seconds: int = 0
    evidence: dict[str, Any] = field(default_factory=dict)
    next_required_conditions: list[str] = field(default_factory=list)
    abort_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
