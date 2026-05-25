from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v66_btcd_scenario_analyzer import analyze_v66_btcd_scenarios, load_true_walk_forward_journal


def run_v66_btcd_rolling_balanced_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    journal = load_true_walk_forward_journal(reports_dir)
    full = analyze_v66_btcd_scenarios(journal, initial_cash_krw, archive_dir)
    subset = {
        "schema_version": "v66_btcd_rolling_balanced_v1",
        "scenarios": [
            row for row in full["scenarios"]
            if row["scenario"] in {"CONTROL_EXISTING", "ROLLING_EDGE_BTCD_OVERLAY", "BALANCED_GROWTH_BTCD_OVERLAY", "POLICY_BLEND_BTCD_ROUTER"}
        ],
        "saved_loss_missed_profit": [
            row for row in full["saved_loss_missed_profit"]
            if row["scenario"] in {"ROLLING_EDGE_BTCD_OVERLAY", "BALANCED_GROWTH_BTCD_OVERLAY", "POLICY_BLEND_BTCD_ROUTER"}
        ],
        "yearly_comparison": full["yearly_comparison"],
        "data_quality": full["data_quality"],
        "audit": full["audit"],
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v66_btcd_rolling_balanced_summary.json", subset)
    _write(Path("replay_store/v66_btcd/latest_v66_btcd_full_summary.json"), full)
    return subset


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

