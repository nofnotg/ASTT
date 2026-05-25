from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from replay_lab.research.v66_btcd_bear_regime_lab import _load_or_build_full


def build_v66_btcd_scenario_comparison(
    reports_dir: str = "docs/reports",
    initial_cash_krw: float = 500000.0,
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    full = _load_or_build_full(initial_cash_krw, reports_dir, archive_dir)
    comparison = {
        "schema_version": "v66_btcd_scenario_comparison_v1",
        "scenarios": full.get("scenarios", []),
        "bear_focus_period": full.get("bear_focus_period", []),
        "saved_loss_missed_profit": full.get("saved_loss_missed_profit", []),
        "yearly_comparison": full.get("yearly_comparison", []),
        "signal_effect": full.get("signal_effect", []),
        "recommendation": full.get("recommendation", {}),
        "audit": full.get("audit", {}),
        "data_quality": full.get("data_quality", {}),
        "equity_curve": full.get("equity_curve", {}),
        "drawdown_curve": full.get("drawdown_curve", {}),
        "btcd_curve": full.get("btcd_curve", []),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    root = Path(reports_dir)
    _write(root / "latest_v66_btcd_scenario_comparison_summary.json", comparison)
    _write(root / "latest_v66_btcd_saved_loss_missed_profit_summary.json", {
        "schema_version": "v66_btcd_saved_loss_missed_profit_v1",
        "saved_loss_missed_profit": comparison["saved_loss_missed_profit"],
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    })
    return comparison


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

