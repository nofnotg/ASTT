from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v685_core import build_bear_window_classification_payload, write_payload


def run_v685_bear_window_classification(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return write_payload(Path(reports_dir) / "latest_v685_bear_window_classification_summary.json", build_bear_window_classification_payload(initial_cash_krw, reports_dir))
