from __future__ import annotations

import json
from pathlib import Path

from replay_lab.research.redesigned_candidate_source_validation_v558 import validate_redesigned_candidate_sources_v558


def validate_full_seed_winner_candidates_v558(reports_dir: str | Path = "docs/reports", initial_cash_krw: float = 500000) -> dict:
    validation = validate_redesigned_candidate_sources_v558()
    rows = []
    for row in validation["source_validation"]:
        grade_b = int(row.get("grade_b_plus", 0))
        rows.append({
            "source": row["source"],
            "candidate": row["candidate"],
            "grade_c": max(0, row["candidate"] - grade_b),
            "grade_b": grade_b,
            "grade_a": 0,
            "grade_s": 0,
            "allocation_candidates": grade_b,
        })
    result = {
        "initial_cash_krw": float(initial_cash_krw),
        "rows": rows,
        "b_a_s_candidate_count": sum(r["grade_b"] + r["grade_a"] + r["grade_s"] for r in rows),
        "allocation_candidate_count": sum(r["allocation_candidates"] for r in rows),
        "real_order_enabled": False,
        "research_mode": True,
        "pnl_evaluable": False,
        "live_readiness": "LIVE_NOT_ALLOWED",
    }
    out = Path("replay_store/winner_mining/reports")
    out.mkdir(parents=True, exist_ok=True)
    (out / "full_seed_winner_candidate_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
