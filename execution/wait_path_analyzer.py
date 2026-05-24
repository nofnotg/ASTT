from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from features.wait_path_features import compute_wait_path_features


def load_session_events(session_dir: str | Path) -> tuple[list[dict], list[dict]]:
    snapshots, candidates = [], []
    ledger = Path(session_dir) / "ledger.jsonl"
    if not ledger.exists():
        return snapshots, candidates
    for line in ledger.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        if event.get("event_type") == "SNAPSHOT":
            snapshots.append(event)
        elif event.get("event_type") == "CANDIDATE":
            candidates.append(event)
    return snapshots, candidates


def analyze_wait_paths(sessions_dir: str | Path) -> dict:
    rows = []
    for session in sorted(Path(sessions_dir).glob("*/ledger.jsonl")):
        snapshots, candidates = load_session_events(session.parent)
        rows.extend(compute_wait_path_features(candidate, snapshots) for candidate in candidates)
    by_class = Counter(row["wait_classification"] for row in rows)
    by_source = defaultdict(list)
    for row in rows:
        by_source[row["candidate_source"]].append(row)
    source_stats = {
        source: {
            "candidate_count": len(items),
            "avg_best_mfe_pct": _avg([i["best_mfe_pct"] for i in items]),
            "avg_worst_mae_pct": _avg([i["worst_mae_pct"] for i in items]),
            "missed_win_count": sum(1 for i in items if i["wait_classification"] == "MISSED_WIN"),
        }
        for source, items in by_source.items()
    }
    return {"candidate_count": len(rows), "rows": rows, "classification_counts": dict(by_class), "source_stats": source_stats, "research_only": True, "included_in_pnl": False}


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0
