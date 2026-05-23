from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from adapters.upbit_public_websocket import subscribe_upbit_ws
from live_data.upbit_ws_message_normalizer import normalize_upbit_orderbook_message, normalize_upbit_trade_message
from replay_lab.paths import REPLAY_STORE_DIR


def run_upbit_real_ws_session(markets: list[str], duration_seconds: int = 300, output_dir: str = "replay_store/raw/upbit_ws", include_trade: bool = True, include_orderbook: bool = True) -> dict:
    session_id = datetime.utcnow().strftime("upbit_ws_%Y%m%d_%H%M%S")
    root = REPLAY_STORE_DIR
    date_part = datetime.utcnow().date().isoformat()
    raw_root = root / "raw" / "upbit_ws" / date_part / session_id
    counts = {"trade": 0, "orderbook": 0}
    by_market = {"trade": {}, "orderbook": {}}
    warnings: list[str] = []

    def on_raw(raw: dict) -> None:
        kind = raw.get("type")
        if kind == "trade":
            event = normalize_upbit_trade_message(raw)
            _write(raw_root / "trades" / f"{event['market']}.jsonl", event)
            counts["trade"] += 1
            by_market["trade"][event["market"]] = by_market["trade"].get(event["market"], 0) + 1
        elif kind == "orderbook":
            event = normalize_upbit_orderbook_message(raw)
            _write(raw_root / "orderbooks" / f"{event['market']}.jsonl", event)
            counts["orderbook"] += 1
            by_market["orderbook"][event["market"]] = by_market["orderbook"].get(event["market"], 0) + 1

    started = datetime.utcnow()
    types = []
    if include_trade:
        types.append("trade")
    if include_orderbook:
        types.append("orderbook")
    result = subscribe_upbit_ws(markets, types, duration_seconds, on_raw)
    warnings.extend(result.get("warnings", []))
    ended = datetime.utcnow()
    summary = {
        "session_id": session_id,
        "data_source": "UPBIT_WS",
        "eligible_for_live_readiness": True,
        "mock_data_used": False,
        "markets": markets,
        "duration_seconds": duration_seconds,
        "trade_event_count": counts["trade"],
        "orderbook_event_count": counts["orderbook"],
        "trade_event_count_by_market": by_market["trade"],
        "orderbook_event_count_by_market": by_market["orderbook"],
        "started_at": started.isoformat(),
        "ended_at": ended.isoformat(),
        "status": "COMPLETED" if counts["trade"] or counts["orderbook"] else "FAILED",
        "warnings": warnings,
        "raw_jsonl_created": bool(list(raw_root.glob("**/*.jsonl"))),
    }
    session_dir = root / "sessions" / "upbit_ws" / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "session_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return summary


def _write(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
