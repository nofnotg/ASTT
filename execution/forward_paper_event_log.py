from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from replay_lab.paths import REPLAY_STORE_DIR


class ForwardPaperEventLog:
    def __init__(self, session_id: str, root: Path = REPLAY_STORE_DIR):
        self.session_id = session_id
        self.path = root / "sessions" / "live_micro" / session_id / "forward_paper_events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, market: str, state_before: str, state_after: str, price: float = 0.0, reason=None, veto_reasons=None, context=None, timestamp_ms: int | None = None) -> dict:
        event = {"session_id": self.session_id, "event_id": str(uuid4()), "event_type": event_type, "timestamp_ms": timestamp_ms or int(datetime.utcnow().timestamp() * 1000), "market": market, "state_before": state_before, "state_after": state_after, "price": price, "reason": reason or [], "veto_reasons": veto_reasons or [], "context": context or {}}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        return event

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]
