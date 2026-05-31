from __future__ import annotations

from pathlib import Path
from typing import Any

from analysis.v686_core import build_v686_atr_model_comparison_payload, build_v686_atr_precision_v2_payload, persist_payload


def run_v686_atr_precision_v2(initial_cash_krw: float = 500000.0, reports_dir: str | Path = "docs/reports") -> dict[str, Any]:
    payload = persist_payload("latest_v686_atr_precision_v2_summary.json", build_v686_atr_precision_v2_payload(initial_cash_krw, reports_dir), reports_dir)
    persist_payload("latest_v686_atr_model_comparison_summary.json", build_v686_atr_model_comparison_payload(initial_cash_krw, reports_dir), reports_dir)
    return payload
