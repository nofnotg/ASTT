from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.event_clip_store import EventClipStore
from timing_lab.event_detector import EventDetector
from timing_lab.market_recorder import MarketRecorder


def replay_timing_lab_v5r1(sessions_dir: str | Path, buffer_minutes: int = 30, post_event_minutes: int = 30) -> dict[str, Any]:
    session_roots = _session_roots(Path(sessions_dir))
    recorder = MarketRecorder(buffer_minutes)
    for root in session_roots:
        for row in _read_session_rows(root):
            recorder.record(row)
    if not recorder.buffer.markets():
        fallback_roots = _session_roots(REPLAY_STORE_DIR / "live_v5510")
        for root in fallback_roots:
            for row in _read_session_rows(root):
                recorder.record(row)
        session_roots = fallback_roots
    detector = EventDetector()
    events: list[dict[str, Any]] = []
    for market in recorder.buffer.markets():
        events.extend(detector.detect(recorder.buffer, market))
    session_id = "recorded_v5r1"
    store = EventClipStore(REPLAY_STORE_DIR / "timing_clips")
    clips = [store.create_clip(session_id, event, recorder.buffer, 600, post_event_minutes * 60, "RECORDED_REPLAY") for event in events]
    summary = {
        "schema_version": "v5r1",
        "mode": "RECORDED_REPLAY",
        "event_count": len(events),
        "clip_count": len(clips),
        "events_by_type": _counts(events, "event_type"),
        "clip_quality_counts": _counts(clips, "quality"),
        "markets_covered": len({event["market"] for event in events}),
        "duration_minutes": buffer_minutes,
        "real_order_enabled": False,
        "source_roots": [str(root) for root in session_roots],
    }
    _write_json(REPLAY_STORE_DIR / "timing_lab" / "latest_timing_lab_summary.json", summary)
    return summary


def _session_roots(path: Path) -> list[Path]:
    roots = [item for item in path.glob("*") if item.is_dir()] if path.exists() else []
    if roots:
        return roots
    fallback = REPLAY_STORE_DIR / "live_v5510"
    return [item for item in fallback.glob("live_v5510_*") if item.is_dir()] if fallback.exists() else []


def _read_session_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pattern in ["trades/*.jsonl", "orderbooks/*.jsonl", "tickers/*.jsonl", "*.jsonl"]:
        for path in root.glob(pattern):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    raw = row.get("raw", {}) if isinstance(row.get("raw"), dict) else {}
                    if not row.get("timestamp_ms"):
                        row["timestamp_ms"] = int(raw.get("trade_timestamp") or raw.get("timestamp") or 0)
                    if not row.get("type"):
                        row["type"] = raw.get("type")
                    rows.append(row)
    return sorted(rows, key=lambda item: int(item.get("timestamp_ms", 0)))


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key, "UNKNOWN")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
