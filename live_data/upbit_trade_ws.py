from __future__ import annotations

import json
from pathlib import Path

from live_data.websocket_schema import normalize_trade_tick


def build_trade_subscribe_message(markets: list[str]) -> list[dict]:
    return [{"ticket": "astt-paper-recorder"}, {"type": "trade", "codes": markets}]


def write_trade_tick(path: Path, payload: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = normalize_trade_tick(payload)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
