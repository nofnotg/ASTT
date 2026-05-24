from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


def validate_full_seed_refined_sources_v559(reports_dir: str = "docs/reports", initial_cash_krw: float = 500000) -> dict:
    forward_path = REPLAY_STORE_DIR / "forward_v559" / "latest_forward_summary.json"
    forward = json.loads(forward_path.read_text(encoding="utf-8")) if forward_path.exists() else {"candidate_by_source": {}, "ENTER": 0}
    quality_blocked = "QUALITY_WINNER_COUNT_ZERO" in set(forward.get("source_quality_flags", []))
    rows = []
    for source, count in forward.get("candidate_by_source", {}).items():
        allocation_candidate = 0 if quality_blocked else count
        rows.append({
            "source": source,
            "candidate": count,
            "grade_c": count if quality_blocked else (0 if count else 1),
            "grade_b": 0 if quality_blocked else count,
            "grade_a": 0,
            "grade_s": 0,
            "allocation_candidate": allocation_candidate,
            "ENTER": 0 if quality_blocked else (forward.get("ENTER", 0) if count else 0),
        })
    result = {
        "initial_cash_krw": initial_cash_krw,
        "rows": rows,
        "quality_blocked": quality_blocked,
        "real_order_enabled": False,
        "research_mode": True,
        "pnl_evaluable": bool(forward.get("paper_trade_count", 0)),
    }
    out = REPLAY_STORE_DIR / "false_positive" / "full_seed_refined_source_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
