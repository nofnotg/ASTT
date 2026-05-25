from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from portfolio.causal_equity_defense_runner import run_causal_scenarios


def run_v64_causal_defense_rerun(initial_cash_krw: float = 500000, use_available_history: bool = True) -> dict[str, Any]:
    summary = run_causal_scenarios(initial_cash_krw=initial_cash_krw)
    summary["use_available_history"] = bool(use_available_history)
    _write(Path("docs/reports/latest_v64_causal_defense_summary.json"), summary)
    return summary


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
