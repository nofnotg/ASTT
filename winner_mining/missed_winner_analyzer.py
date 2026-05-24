from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def analyze_missed_winners(winner_traces_path: str | Path) -> dict:
    traces = _load_traces(winner_traces_path)
    missed = [trace for trace in traces if trace.get("feature_quality") != "POOR"]
    patterns = _patterns(missed)
    result = {"missed_winner_count": len(missed), "common_patterns": patterns, "recommendations": [p["suggested_candidate_source"] for p in patterns], "main_reason_existing_sources_failed": "Existing gates emphasized immediate micro strength; several winner traces show volume/range preconditions before strict acceleration."}
    out = REPLAY_STORE_DIR / "winner_mining" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "missed_winner_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _patterns(traces: list[dict]) -> list[dict]:
    checks = {
        "VOLUME_THEN_BREAKOUT": lambda f: f.get("volume_burst_ratio_10s_vs_60s", 0) >= 1.2 and f.get("range_position_pct", 0) >= 60,
        "ORDERFLOW_SURGE": lambda f: f.get("buy_trade_ratio_10s", 0) >= 0.55,
        "RANGE_COMPRESSION_EXPANSION": lambda f: f.get("previous_high_distance_pct", 999) <= 0.3,
    }
    rows = []
    for pattern_id, check in checks.items():
        count = sum(1 for trace in traces if check(trace.get("trace_windows", {}).get("T_MINUS_10S", {})))
        rows.append({"pattern_id": pattern_id, "description": pattern_id.replace("_", " ").title(), "support_count": count, "support_pct": count / len(traces) if traces else 0.0, "suggested_candidate_source": pattern_id})
    return rows


def _load_traces(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.is_dir():
        path = path / "winner_traces.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("traces", data if isinstance(data, list) else [])
