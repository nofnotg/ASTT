from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v673_agent_matrix_analyzer import analyze_v673_agent_matrix
from analysis.v673_scenario_agent_router_analyzer import extract_v673_router


def run_v673_scenario_agent_router_lab(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    matrix = analyze_v673_agent_matrix(initial_cash_krw, reports_dir, archive_dir)
    payload = extract_v673_router(matrix)
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v673_scenario_router_summary.json", payload)
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
