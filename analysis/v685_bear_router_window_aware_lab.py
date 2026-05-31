from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v685_core import build_bear_router_window_aware_payload, write_payload


def run_v685_bear_router_window_aware_lab(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return write_payload(Path(reports_dir) / "latest_v685_bear_router_window_aware_summary.json", build_bear_router_window_aware_payload(initial_cash_krw, reports_dir))
