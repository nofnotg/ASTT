from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v673_agent_matrix_analyzer import analyze_v673_agent_matrix


def run_v673_rolling_balanced_dominance_matrix_lab(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str = "docs/reports",
    archive_dir: str = "replay_store/historical_archive",
) -> dict[str, Any]:
    summary = analyze_v673_agent_matrix(initial_cash_krw, reports_dir, archive_dir)
    matrix_names = {
        "ROLLING_ONLY_CONTROL",
        "ROLLING_ONLY_DOMINANCE_OVERLAY",
        "BALANCED_ONLY_CONTROL",
        "BALANCED_ONLY_DOMINANCE_OVERLAY",
        "POLICY_BLEND_CONTROL",
        "POLICY_BLEND_DOMINANCE_OVERLAY",
    }
    payload = dict(summary)
    payload["schema_version"] = "v673_agent_matrix_v1"
    payload["scenarios"] = [row for row in summary.get("scenarios", []) if row.get("scenario") in matrix_names]
    payload["use_available_history"] = use_available_history
    _write(Path(reports_dir) / "latest_v673_agent_matrix_summary.json", payload)
    return payload


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
