from __future__ import annotations

import json
from pathlib import Path

from live_data.websocket_schema import normalize_orderbook_tick


def build_orderbook_subscribe_message(markets: list[str]) -> list[dict]:
    return [{"ticket": "astt-paper-recorder"}, {"type": "orderbook", "codes": markets}]


def write_orderbook_tick(path: Path, payload: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = normalize_orderbook_tick(payload)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
