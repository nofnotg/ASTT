from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR


@dataclass
class LiveMicroStorage:
    session_id: str
    root: Path = REPLAY_STORE_DIR
    dropped_event_count: int = 0
    trade_event_count: int = 0
    orderbook_event_count: int = 0
    markets: set[str] = field(default_factory=set)

    @property
    def session_dir(self) -> Path:
        return self.root / "sessions" / "live_micro" / self.session_id

    def append_trade(self, event: dict) -> None:
        event = {"session_id": self.session_id, "type": "trade", "received_at_ms": _now_ms(), **event}
        self._append("trades", event)
        self.trade_event_count += 1

    def append_orderbook(self, event: dict) -> None:
        event = {"session_id": self.session_id, "type": "orderbook", "received_at_ms": _now_ms(), **event}
        self._append("orderbooks", event)
        self.orderbook_event_count += 1

    def normalize_to_parquet(self) -> None:
        for kind in ["trades", "orderbooks"]:
            for path in (self.root / "raw" / "live_micro").glob(f"*/{kind}/*.jsonl"):
                rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
                if not rows or rows[0].get("session_id") != self.session_id:
                    continue
                date_part = path.parts[-3]
                out = self.root / "normalized" / "live_micro" / date_part / kind
                out.mkdir(parents=True, exist_ok=True)
                frame = pd.DataFrame(rows)
                for column in ["raw", "units"]:
                    if column in frame:
                        frame[column] = frame[column].apply(lambda value: json.dumps(value, ensure_ascii=False, default=str))
                frame.to_parquet(out / f"{path.stem}.parquet", index=False)

    def write_summary(self, **extra) -> Path:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": self.session_id,
            "markets": sorted(self.markets),
            "trade_event_count": self.trade_event_count,
            "orderbook_event_count": self.orderbook_event_count,
            "dropped_event_count": self.dropped_event_count,
            **extra,
        }
        path = self.session_dir / "session_summary.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return path

    def _append(self, kind: str, event: dict) -> None:
        try:
            market = event.get("market", "UNKNOWN")
            self.markets.add(market)
            date_part = datetime.utcfromtimestamp(event.get("timestamp_ms", _now_ms()) / 1000).date().isoformat()
            path = self.root / "raw" / "live_micro" / date_part / kind / f"{market}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        except Exception:
            self.dropped_event_count += 1


def _now_ms() -> int:
    return int(datetime.utcnow().timestamp() * 1000)
