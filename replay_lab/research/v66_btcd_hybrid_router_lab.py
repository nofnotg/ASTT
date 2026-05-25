from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from replay_lab.research.v66_btcd_bear_regime_lab import _load_or_build_full


def run_v66_btcd_hybrid_router_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    full = _load_or_build_full(initial_cash_krw, reports_dir, archive_dir)
    row = next((item for item in full["scenarios"] if item["scenario"] == "HYBRID_BEAR_ROUTER_BTCD"), {})
    summary = {
        "schema_version": "v66_btcd_hybrid_router_v1",
        "scenario": row,
        "saved_loss_missed_profit": next((item for item in full["saved_loss_missed_profit"] if item["scenario"] == "HYBRID_BEAR_ROUTER_BTCD"), {}),
        "recommendation": full.get("recommendation", {}),
        "audit": full.get("audit", {}),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v66_btcd_hybrid_router_summary.json", summary)
    return summary


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

