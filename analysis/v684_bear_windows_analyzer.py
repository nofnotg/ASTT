from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v684_bear_indicator_core import build_bear_windows_payload, write_payload


def run_v684_bear_windows(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    return write_payload(Path(reports_dir) / "latest_v684_bear_windows_summary.json", build_bear_windows_payload(initial_cash_krw, reports_dir))
