from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v66_btcd_scenario_analyzer import analyze_v66_btcd_scenarios, load_true_walk_forward_journal


def run_v66_btcd_bear_regime_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    full = _load_or_build_full(initial_cash_krw, reports_dir, archive_dir)
    subset = {
        "schema_version": "v66_btcd_bear_regime_v1",
        "scenarios": [
            row for row in full["scenarios"]
            if row["scenario"] in {"CONTROL_EXISTING", "BEAR_DEFENSE_BTCD", "BEAR_BOUNCE_BTCD", "RELATIVE_STRENGTH_BTCD", "HYBRID_BEAR_ROUTER_BTCD"}
        ],
        "bear_focus_period": full["bear_focus_period"],
        "focus_2024_11": full["focus_2024_11"],
        "audit": full["audit"],
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v66_btcd_bear_scenario_summary.json", subset)
    _write(Path(reports_dir) / "latest_v66_btcd_2024_11_focus_summary.json", {
        "schema_version": "v66_btcd_2024_11_focus_v1",
        "bear_focus_period": full["bear_focus_period"],
        "focus_2024_11": full["focus_2024_11"],
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    })
    return subset


def run_v66_btcd_bear_bounce_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    full = _load_or_build_full(initial_cash_krw, reports_dir, archive_dir)
    row = next((item for item in full["scenarios"] if item["scenario"] == "BEAR_BOUNCE_BTCD"), {})
    summary = {
        "schema_version": "v66_btcd_bear_bounce_v1",
        "scenario": row,
        "decision": row.get("decision", "BTCD_FILTER_REJECTED"),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v66_btcd_bear_bounce_summary.json", summary)
    return summary


def _load_or_build_full(initial_cash_krw: float, reports_dir: str, archive_dir: str) -> dict[str, Any]:
    full_path = Path("replay_store/v66_btcd/latest_v66_btcd_full_summary.json")
    if full_path.exists():
        return json.loads(full_path.read_text(encoding="utf-8-sig"))
    journal = load_true_walk_forward_journal(reports_dir)
    full = analyze_v66_btcd_scenarios(journal, initial_cash_krw, archive_dir)
    _write(full_path, full)
    return full


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

