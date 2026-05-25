from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.v64_scenario_comparator import compare_v64_scenarios


def build_v64_scenario_comparison(reports_dir: str = "docs/reports") -> dict[str, Any]:
    root = Path(reports_dir)
    causal = _read(root / "latest_v64_causal_defense_summary.json")
    summary = compare_v64_scenarios(causal)
    _write(root / "latest_v64_scenario_comparison_summary.json", summary)
    return summary


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
