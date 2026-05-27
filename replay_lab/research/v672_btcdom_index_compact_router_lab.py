from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v672_btcdom_index_scenario_analyzer import analyze_v672_btcdom_index_scenarios


def run_v672_btcdom_index_compact_router_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    full = analyze_v672_btcdom_index_scenarios(initial_cash_krw=initial_cash_krw, reports_dir=reports_dir, archive_dir=archive_dir)
    scenario = next((row for row in full.get("scenarios", []) if row.get("scenario") == "BTCDOM_INDEX_COMPACT_ROUTER"), {})
    saved = next((row for row in full.get("saved_loss_missed_profit", []) if row.get("scenario") == "BTCDOM_INDEX_COMPACT_ROUTER"), {})
    payload = {
        "schema_version": "v672_btcdom_index_compact_router_v1",
        "scenario": scenario,
        "saved_loss_missed_profit": saved,
        "audit": full.get("audit", {}),
        "decision": scenario.get("decision", "BTCDOM_INDEX_DATA_REQUIRED"),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }
    _write(Path(reports_dir) / "latest_v672_btcdom_index_compact_router_summary.json", payload)
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
