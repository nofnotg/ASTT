from __future__ import annotations

from pathlib import Path

from features.micro_cost_model import SCENARIOS
from replay_lab.research.forward_micro_validation import validate_forward_micro_sessions


def run_micro_cost_survival_test(sessions_dir: str | Path, min_quality: str = "PARTIAL") -> dict:
    validation = validate_forward_micro_sessions(sessions_dir, min_quality=min_quality)
    base = validation["results"].get("GOOD_PLUS_PARTIAL", {})
    results = []
    for scenario in SCENARIOS:
        factor = {"gross": 1.0, "fee_only": 0.8, "realistic_1": 0.55, "realistic_2": 0.3, "stress": 0.15}[scenario]
        pf = float(base.get("profit_factor_gross", 0.0)) * factor
        expectancy = float(base.get("expectancy_realistic_1", 0.0)) * factor
        pnl = float(base.get("total_pnl_krw_realistic_1", 0.0)) * factor
        results.append({"scenario": scenario, "profit_factor": pf, "expectancy_pct": expectancy, "pnl_krw": pnl, "survives": pf >= 1.1 and expectancy > 0 and pnl > 0})
    realistic = next(r for r in results if r["scenario"] == "realistic_1")
    return {"results": results, "realistic_1_survives": realistic["survives"], "live_readiness": "PAPER_MORE_REQUIRED" if realistic["survives"] else "LIVE_NOT_ALLOWED"}
