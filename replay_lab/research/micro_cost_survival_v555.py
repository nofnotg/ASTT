from __future__ import annotations

import json
from pathlib import Path

from execution.realistic_paper_fill_model import SCENARIOS
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.realistic_paper_validation_v555 import validate_realistic_paper_v555


def test_micro_cost_survival_v555(sessions_dir: str | Path = REPLAY_STORE_DIR / "sessions" / "realistic_paper_v555") -> dict:
    base = validate_realistic_paper_v555(sessions_dir)
    rows = []
    for scenario in SCENARIOS:
        rows.append({"scenario": scenario, "pf": base["profit_factor"], "expectancy": base["expectancy_pct"], "pnl_krw": base["total_pnl_krw"], "survives": base["trade_count"] >= 20 and base["profit_factor"] >= 1.1 and (base["expectancy_pct"] or 0) > 0 and base["total_pnl_krw"] > 0})
    result = {"scenarios": rows, "realistic_1_survives": next(row["survives"] for row in rows if row["scenario"] == "realistic_1")}
    out = REPLAY_STORE_DIR / "reports" / "realistic_paper_v555"
    out.mkdir(parents=True, exist_ok=True)
    (out / "micro_cost_survival.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result
