from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v672_btcdom_index_scenario_analyzer import analyze_v672_btcdom_index_scenarios


def run_v672_btcdom_index_scenario_lab(
    initial_cash_krw: float = 500000.0,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    summary = analyze_v672_btcdom_index_scenarios(initial_cash_krw=initial_cash_krw, reports_dir=reports_dir, archive_dir=archive_dir)
    _write(Path(reports_dir) / "latest_v672_btcdom_index_scenario_summary.json", summary)
    return summary


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
