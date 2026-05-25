from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v65_ma_scenario_analyzer import analyze_v65_ma_scenarios, load_true_walk_forward_journal


def run_v65_ma_scenario_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    root = Path(reports_dir)
    journal = load_true_walk_forward_journal(root)
    summary = analyze_v65_ma_scenarios(journal, initial_cash_krw, archive_dir)
    _write(root / "latest_v65_ma_scenario_summary.json", summary)
    store = Path("replay_store/v65_ma")
    store.mkdir(parents=True, exist_ok=True)
    _write(store / "latest_v65_ma_scenario_summary.json", summary)
    return summary


def run_v65_ma_policy_router_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    scenario = run_v65_ma_scenario_lab(initial_cash_krw, reports_dir, archive_dir)
    router = {
        "schema_version": "v65_ma_policy_router_v1",
        "best_scenario": scenario.get("recommendation", {}).get("best_scenario"),
        "router": scenario.get("policy_router", {}),
        "scenario_rows": [
            row for row in scenario.get("scenarios", []) if row.get("scenario") in {"CONTROL_CURRENT_ROUTER", "MA_POLICY_ROUTER", "MA_DEFENSIVE_REPAIR"}
        ],
        "yearly_comparison": scenario.get("yearly_comparison", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v65_ma_policy_router_summary.json", router)
    return router


def analyze_v65_yearly_weakness_repair(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v65_ma_scenario_summary.json")
    weak = {
        "schema_version": "v65_yearly_repair_v1",
        "yearly_comparison": scenario.get("yearly_comparison", []),
        "weak_year_repair": scenario.get("weak_year_repair", {}),
        "plan_impact": scenario.get("plan_impact", []),
        "recommendation": scenario.get("recommendation", {}),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(root / "latest_v65_yearly_repair_summary.json", weak)
    return weak


def build_v65_ma_risk_report(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    scenario = _read(root / "latest_v65_ma_scenario_summary.json")
    risk = {
        "schema_version": "v65_ma_risk_v1",
        "scenario_risk": scenario.get("risk_summary", {}),
        "ma_condition_effect": scenario.get("ma_condition_effect", []),
        "audit": scenario.get("audit", {}),
        "final_judgement": scenario.get("recommendation", {}).get("final_judgement", "LIVE_NOT_ALLOWED"),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(root / "latest_v65_ma_risk_summary.json", risk)
    return risk


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
