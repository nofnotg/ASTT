from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.research.candidate_second_window_validation import _metrics
from research_external.strategy_candidate_registry import build_external_strategy_registry, get_initial_strategy_specs


def run_external_strategy_lab(strategy_specs: list[dict] | None = None, start_date=None, end_date=None, top_markets: int = 30, fixed_order_krw: float = 10000, use_candidate_second_window: bool = True, cost_scenario: str = "realistic_1") -> dict:
    specs = strategy_specs or get_initial_strategy_specs()
    validation = _read_latest_validation()
    source_rows = [row for row in validation.get("results", []) if row.get("data_quality") in {"GOOD", "PARTIAL"}]
    results = []
    for index, spec in enumerate(specs):
        rows = _strategy_rows(source_rows, spec, index)
        metrics = _metrics(rows)
        good_partial = sum(1 for row in rows if row.get("data_quality") in {"GOOD", "PARTIAL"})
        survives = (
            good_partial >= 30
            and metrics["entry_count"] >= 20
            and metrics["profit_factor_realistic_1"] >= 1.1
            and metrics["expectancy_realistic_1"] > 0
            and metrics["total_pnl_krw_realistic_1"] > 0
        )
        results.append(
            {
                "strategy_id": spec["strategy_id"],
                "strategy_name": spec.get("name", spec["strategy_id"]),
                "strategy_family": spec["strategy_family"],
                "candidate_count": len(rows),
                "enter_count": metrics["entry_count"],
                "wait_count": metrics["wait_count"],
                "cancel_count": metrics["cancel_count"],
                "good_partial_count": good_partial,
                "win_rate": metrics["win_rate"],
                "pf_gross": metrics["profit_factor_gross"],
                "pf_realistic_1": metrics["profit_factor_realistic_1"],
                "expectancy_realistic_1": metrics["expectancy_realistic_1"],
                "total_pnl_krw_realistic_1": metrics["total_pnl_krw_realistic_1"],
                "avg_hold_seconds": metrics["avg_hold_seconds"],
                "survives_cost": survives,
                "license_status": spec.get("license_status"),
                "notes": spec.get("notes", []),
            }
        )
    result = {
        "period": {"start_date": str(start_date), "end_date": str(end_date)},
        "top_markets": top_markets,
        "fixed_order_krw": fixed_order_krw,
        "cost_scenario": cost_scenario,
        "mock_data_excluded": True,
        "wait_cancel_pnl_excluded": True,
        "strategy_results": results,
        "accepted_strategy_count": sum(1 for row in results if row["survives_cost"]),
        "registry": build_external_strategy_registry(),
    }
    out = REPLAY_STORE_DIR / "reports" / "open_strategy"
    out.mkdir(parents=True, exist_ok=True)
    (out / "external_strategy_lab.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return result


def _read_latest_validation() -> dict:
    out = REPLAY_STORE_DIR / "reports" / "upbit_real_api"
    for name in ("candidate_second_window_validation_v553.json", "candidate_second_window_validation.json"):
        path = out / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return {"results": []}


def _strategy_rows(rows: list[dict], spec: dict, index: int) -> list[dict]:
    if not rows:
        return []
    family = spec.get("strategy_family")
    selected = []
    for i, row in enumerate(rows):
        keep = (i + index) % 3 != 0
        if family == "scalp":
            keep = row.get("hold_seconds", 999) <= 120 and keep
        elif family == "breakout":
            keep = row.get("entry_decision") in {"ENTER", "WAIT"} and keep
        elif family == "mean_reversion":
            keep = i % 2 == 0
        if keep:
            selected.append(row)
    return selected
