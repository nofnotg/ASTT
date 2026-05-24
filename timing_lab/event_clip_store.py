from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from timing_lab.event_clip_schema import EventClipMeta
from timing_lab.ring_buffer import MarketRingBuffer


class EventClipStore:
    def __init__(self, root: str | Path = "replay_store/timing_clips"):
        self.root = Path(root)

    def create_clip(
        self,
        session_id: str,
        event: dict[str, Any],
        buffer: MarketRingBuffer,
        pre_window_seconds: int = 600,
        post_window_seconds: int = 1800,
        source: str = "RECORDED_REPLAY",
    ) -> dict[str, Any]:
        event_time = int(event["event_time_ms"])
        market = event["market"]
        clip_id = f"{event['event_id']}_clip"
        rows = buffer.extract_clip(market, event_time, pre_window_seconds, post_window_seconds)
        counts = {"trade": 0, "orderbook": 0, "ticker": 0}
        for row in rows:
            if row.get("type") in counts:
                counts[row["type"]] += 1
        has_post = any(int(row.get("timestamp_ms", 0)) > event_time for row in rows)
        quality = "GOOD" if counts["trade"] and counts["orderbook"] and has_post else "PARTIAL" if rows else "POOR"
        meta = EventClipMeta(
            clip_id=clip_id,
            event_id=event["event_id"],
            market=market,
            event_type=event["event_type"],
            event_time_ms=event_time,
            clip_start_ms=event_time - pre_window_seconds * 1000,
            clip_end_ms=event_time + post_window_seconds * 1000,
            pre_window_seconds=pre_window_seconds,
            post_window_seconds=post_window_seconds,
            trade_event_count=counts["trade"],
            orderbook_event_count=counts["orderbook"],
            ticker_event_count=counts["ticker"],
            quality=quality,
            source=source,
            status="CLOSED" if has_post else "OPEN",
        ).to_dict()
        clip_dir = self.root / session_id / clip_id
        clip_dir.mkdir(parents=True, exist_ok=True)
        (clip_dir / "clip_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        for name, kind in [("trades.jsonl", "trade"), ("orderbooks.jsonl", "orderbook"), ("tickers.jsonl", "ticker")]:
            with (clip_dir / name).open("w", encoding="utf-8") as handle:
                for row in rows:
                    if row.get("type") == kind:
                        handle.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return meta

    def list_clips(self) -> list[dict[str, Any]]:
        clips: list[dict[str, Any]] = []
        for path in self.root.glob("*/*/clip_meta.json"):
            clips.append(json.loads(path.read_text(encoding="utf-8")))
        return clips


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
