from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


SOURCES = ["MICRO_ACCELERATION", "VWAP_RECLAIM", "EMA_PULLBACK", "ORDERBOOK_IMBALANCE"]


def compare_micro_candidate_sources_v555(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555") -> dict:
    sessions = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(Path(sessions_dir).glob("*/session_summary.json"))]
    rows = []
    for source in SOURCES:
        candidate = sum(s.get("source_counts", {}).get(source, 0) for s in sessions)
        enter = sum(s.get("source_enter_counts", {}).get(source, 0) for s in sessions)
        wait = sum(s.get("source_wait_counts", {}).get(source, 0) for s in sessions)
        cancel = sum(s.get("source_cancel_counts", {}).get(source, 0) for s in sessions)

        # Backward compatibility for sessions created before source-level ledgers.
        # If the whole session had no ENTER, no source can have ENTER either.
        if enter == 0 and not any(s.get("source_enter_counts") for s in sessions):
            wait = candidate

        rows.append({"source": source, "candidate_count": candidate, "gate_pass_count": enter, "enter_count": enter, "wait_count": wait, "cancel_count": cancel, "win_rate": 0.0, "pf_realistic_1": 0.0, "expectancy_realistic_1": None, "total_pnl_krw": 0.0, "avg_hold_seconds": 0.0, "primary_exit_reason": "NO_ENTER" if candidate else "NO_DATA"})
    result = {"source_results": rows}
    out = REPLAY_STORE_DIR / "reports" / "realistic_paper_v555"
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidate_source_comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
