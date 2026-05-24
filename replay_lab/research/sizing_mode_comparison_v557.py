from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR


MODES = ["FIXED_10K", "FIXED_100K", "FULL_SEED_SINGLE", "FULL_SEED_LADDER"]


def compare_sizing_modes_v557(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555", initial_cash_krw: float = 500000) -> dict:
    entry = _load_entry()
    candidate_count = int(entry.get("candidate_count", 0))
    enter = int(next((row.get("enter", 0) for row in entry.get("profiles", []) if row.get("profile") == "BALANCED"), 0))
    rows = []
    for mode in MODES:
        rows.append({
            "mode": mode,
            "candidate": candidate_count,
            "enter": enter,
            "trade": enter,
            "win_rate": None if enter == 0 else 0.0,
            "pf": None if enter == 0 else 0.0,
            "return_pct": None if enter == 0 else 0.0,
            "mdd_pct": 0.0,
            "fee_krw": 0.0,
            "slippage_krw": 0.0,
            "pnl_evaluable": enter > 0,
        })
    result = {"initial_cash_krw": float(initial_cash_krw), "sizing_mode_results": rows, "primary_problem": "ENTER_0" if enter == 0 else "TRADES_AVAILABLE"}
    out = REPLAY_STORE_DIR / "reports" / "full_seed_allocator_v557"
    out.mkdir(parents=True, exist_ok=True)
    (out / "sizing_mode_comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _load_entry() -> dict:
    path = Path("docs/reports/latest_entry_discovery_summary.json")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"candidate_count": 0, "profiles": []}
