from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v67_global_btcd_router_comparator import compact_router_summary


def run_v67_global_btcd_compact_router_lab(reports_dir: str = "docs/reports") -> dict[str, Any]:
    scenario_path = Path(reports_dir) / "latest_v67_global_btcd_scenario_summary.json"
    summary = json.loads(scenario_path.read_text(encoding="utf-8-sig")) if scenario_path.exists() else {}
    compact = compact_router_summary(summary)
    _write(Path(reports_dir) / "latest_v67_global_btcd_compact_router_summary.json", compact)
    return compact


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
