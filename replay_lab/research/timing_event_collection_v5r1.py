from __future__ import annotations

import json
from pathlib import Path

from live_capture.upbit_live_ws_collector_v5510 import collect_high_volatility_live_session_v5510
from replay_lab.paths import REPLAY_STORE_DIR
from timing_lab.timing_replay_engine import replay_timing_lab_v5r1


def run_timing_lab_live_v5r1(duration_minutes: int = 60, top_markets: int = 30, buffer_minutes: int = 30, post_event_minutes: int = 30, research_mode: bool = True) -> dict:
    live = collect_high_volatility_live_session_v5510("TIMING_LAB", duration_minutes, top_markets)
    summary = replay_timing_lab_v5r1(REPLAY_STORE_DIR / "live_v5510", buffer_minutes, post_event_minutes)
    payload = {**summary, "mode": "LIVE_TIMING_LAB", "duration_minutes": duration_minutes, "live_session": live, "research_mode": research_mode, "real_order_enabled": False}
    out = REPLAY_STORE_DIR / "timing_lab" / "latest_timing_lab_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return payload
