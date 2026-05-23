from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


VALID_STATES = ["IDLE", "SETUP_FOUND", "ARMED", "ENTERED", "MANAGE", "EXIT", "REVIEW"]


@dataclass
class ResponseStateMachine:
    state: str = "IDLE"
    history: list[dict] = field(default_factory=list)

    def transition(self, next_state: str, reason: str, timestamp=None, context: dict | None = None) -> dict:
        if next_state not in VALID_STATES:
            raise ValueError(f"invalid state: {next_state}")
        previous = self.state
        self.state = next_state
        row = {"state": next_state, "previous_state": previous, "transition_reason": reason, "timestamp": str(timestamp or datetime.utcnow().isoformat()), "context": context or {}}
        self.history.append(row)
        return row

    def on_setup(self, context: dict | None = None) -> dict:
        return self.transition("SETUP_FOUND", "minute_setup_found", context=context)

    def arm_or_idle(self, allowed: bool, reason: str, context: dict | None = None) -> dict:
        return self.transition("ARMED" if allowed else "IDLE", reason, context=context)

    def enter(self, context: dict | None = None) -> dict:
        return self.transition("ENTERED", "paper_entry_filled", context=context)

    def manage(self, context: dict | None = None) -> dict:
        return self.transition("MANAGE", "manage_position", context=context)

    def exit(self, reason: str, context: dict | None = None) -> dict:
        return self.transition("EXIT", reason, context=context)

    def review(self, context: dict | None = None) -> dict:
        return self.transition("REVIEW", "record_result", context=context)
