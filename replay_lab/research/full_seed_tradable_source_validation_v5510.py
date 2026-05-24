from __future__ import annotations

import json

from replay_lab.paths import REPLAY_STORE_DIR


def validate_full_seed_tradable_sources_v5510(reports_dir: str = "docs/reports", initial_cash_krw: float = 500000) -> dict:
    path = REPLAY_STORE_DIR / "tradable_forward" / "latest_tradable_forward_summary.json"
    forward = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"full_seed_grade_rows": []}
    rows = forward.get("full_seed_grade_rows", [])
    result = {
        "initial_cash_krw": initial_cash_krw,
        "default_sizing_mode": "FULL_SEED_LADDER",
        "rows": rows,
        "allocation_candidate_count": sum(int(r.get("allocation_candidate", 0) or 0) for r in rows),
        "real_order_enabled": False,
        "research_mode": True,
    }
    out = REPLAY_STORE_DIR / "tradable_forward" / "full_seed_tradable_source_validation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result
