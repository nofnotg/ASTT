from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analysis.return_amplification_analyzer import analyze_return_amplification


def run_v64_return_amplification_lab(initial_cash_krw: float = 500000, use_available_history: bool = True) -> dict[str, Any]:
    causal = _read(Path("docs/reports/latest_v64_causal_defense_summary.json"))
    if not causal:
        from replay_lab.research.v64_causal_defense_rerun import run_v64_causal_defense_rerun

        causal = run_v64_causal_defense_rerun(initial_cash_krw, use_available_history)
    summary = analyze_return_amplification(causal)
    _write(Path("docs/reports/latest_v64_return_amplification_summary.json"), summary)
    return summary


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
