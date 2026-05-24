from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from timing_lab.event_clip_store import read_jsonl


def analyze_detector_gaps(clips_dir: str | Path) -> dict[str, Any]:
    relaxed_range = 0
    relaxed_breakout = 0
    data_clips = 0
    for meta_path in Path(clips_dir).glob("*/*/clip_meta.json"):
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
        if str(meta.get("market", "")).endswith("TEST"):
            continue
        trades = read_jsonl(meta_path.parent / "trades.jsonl")
        prices = [float(row.get("trade_price") or 0) for row in trades if float(row.get("trade_price") or 0) > 0]
        if len(prices) >= 3:
            data_clips += 1
            high = max(prices[:-1])
            latest = prices[-1]
            if high and abs(latest - high) / high <= 0.003:
                relaxed_range += 1
            if high and latest > high * 0.999:
                relaxed_breakout += 1
    status = "THRESHOLD_TOO_STRICT" if data_clips and (relaxed_range or relaxed_breakout) else "DATA_MISSING"
    summary = {
        "range_touch_detector_status": status,
        "breakout_pressure_detector_status": status,
        "relaxed_range_touch_count": relaxed_range,
        "relaxed_breakout_pressure_count": relaxed_breakout,
        "data_sufficient_clip_count": data_clips,
        "recommended_fix": ["Add relaxed range proximity to calibration grid", "Compute range context from rolling trade prices"],
    }
    _write(Path("replay_store/calibration/detector_gap_analysis.json"), summary)
    return summary


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
