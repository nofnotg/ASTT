from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v685_core import build_atr_sensitivity_payload, write_payload


def run_v685_atr_sensitivity_lab(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return write_payload(Path(reports_dir) / "latest_v685_atr_sensitivity_summary.json", build_atr_sensitivity_payload(initial_cash_krw, reports_dir))
