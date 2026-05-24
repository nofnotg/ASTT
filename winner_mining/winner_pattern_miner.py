from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from winner_mining.missed_winner_analyzer import analyze_missed_winners


PATTERN_IDS = ["VOLUME_RANGE_BREAKOUT", "ORDERFLOW_SURGE", "VWAP_RECLAIM_WITH_VOLUME", "EARLY_VOLUME_ACCUMULATION", "RANGE_COMPRESSION_EXPANSION"]


def mine_winner_patterns(winner_traces_path: str | Path) -> dict:
    missed = analyze_missed_winners(winner_traces_path)
    support_map = {p["pattern_id"]: p for p in missed.get("common_patterns", [])}
    trace_count = max(1, missed.get("missed_winner_count", 0))
    patterns = []
    for pattern_id in PATTERN_IDS:
        base = support_map.get(pattern_id.replace("VOLUME_RANGE_BREAKOUT", "VOLUME_THEN_BREAKOUT"), {})
        support = int(base.get("support_count", 0))
        patterns.append({
            "pattern_id": pattern_id,
            "support_count": support,
            "support_pct": support / trace_count,
            "false_positive_risk": "MEDIUM" if support else "HIGH",
            "candidate_source_spec": {"candidate_source": pattern_id, "research_mode": True, "real_order_enabled": False},
            "requires_forward_validation": True,
            "auto_apply_allowed": False,
        })
    result = {"patterns": patterns, "pattern_count": len(patterns)}
    out = REPLAY_STORE_DIR / "winner_mining" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "winner_patterns.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
