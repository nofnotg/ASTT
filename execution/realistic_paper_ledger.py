from __future__ import annotations

import json
from pathlib import Path


class RealisticPaperLedger:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def append(self, event_type: str, payload: dict) -> dict:
        event = {"event_type": event_type, **payload}
        self._write("ledger.jsonl", event)
        if event_type in {"POSITION_OPENED", "POSITION_CLOSED"}:
            self._write("positions.jsonl", event)
        if event_type == "POSITION_CLOSED":
            self._write("trades.jsonl", event)
        return event

    def write_summary(self, summary: dict) -> None:
        (self.session_dir / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def _write(self, name: str, event: dict) -> None:
        with (self.session_dir / name).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
