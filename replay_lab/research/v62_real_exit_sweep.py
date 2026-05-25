from __future__ import annotations

import json
from pathlib import Path

from analysis.real_exit_sweep import run_real_exit_sweep
from portfolio.trade_journal_builder import build_trade_journal


def run_v62_real_exit_sweep(initial_cash_krw: float = 500000) -> dict:
    journal = build_trade_journal(initial_cash_krw, True)["journal"]
    payload = {"schema_version": "v6.2", "exit_rows": run_real_exit_sweep(journal), "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v62_exit_sweep_summary.json", payload)
    _write("replay_store/v62/latest_v62_exit_sweep_summary.json", payload)
    return payload


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
