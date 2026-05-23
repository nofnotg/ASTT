from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def audit_micro_data_quality(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "live_micro") -> dict:
    root = Path(sessions_dir)
    summaries = _summaries(root)
    quality = {}
    minutes = 0.0
    replayable = 0
    market_coverage = {}
    for item in summaries:
        minutes += float(item.get("duration_minutes", 0.0))
        for grade, count in item.get("data_quality_summary", {}).items():
            quality[grade] = quality.get(grade, 0) + int(count)
        if item.get("trade_event_count", 0) and item.get("orderbook_event_count", 0):
            replayable += 1
        for market in item.get("markets", []):
            market_coverage[market] = market_coverage.get(market, 0) + 1
    return {"session_count": len(summaries), "total_recording_minutes": minutes, "market_coverage": market_coverage, "quality_distribution": quality, "replayable_session_count": replayable, "warnings": [] if summaries else ["no_sessions"]}


def _summaries(root: Path) -> list[dict]:
    if not root.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in root.glob("*/session_summary.json")]
