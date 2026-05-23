from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path


def record_realtime_markets(markets: list[str], duration_minutes: int, output: str) -> dict:
    """Create a recording manifest. Actual websocket streaming is intentionally recording-only."""

    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "markets": markets,
        "duration_minutes": duration_minutes,
        "output": str(out),
        "recording_only": True,
        "orders_enabled": False,
        "created_at": datetime.utcnow().isoformat(),
        "note": "Use upbit_trade_ws/upbit_orderbook_ws writers for live websocket ticks.",
    }
    (out / "recording_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--markets", required=True)
    parser.add_argument("--duration-minutes", type=int, default=60)
    parser.add_argument("--output", default="replay_store/raw/live_ws")
    args = parser.parse_args()
    result = record_realtime_markets([item.strip() for item in args.markets.split(",") if item.strip()], args.duration_minutes, args.output)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
