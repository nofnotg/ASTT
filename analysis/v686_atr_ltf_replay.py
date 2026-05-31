from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v686_core import build_v686_atr_ltf_replay_payload, persist_payload


def run_v686_atr_ltf_replay(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return persist_payload("latest_v686_atr_ltf_replay_summary.json", build_v686_atr_ltf_replay_payload(initial_cash_krw, reports_dir), reports_dir)
