from __future__ import annotations

import json
from pathlib import Path

from portfolio.equity_curve_simulator import load_candidate_trades
from strategy_router.strategy_router import plan_for_trade


def validate_v62_strategy_router(initial_cash_krw: float = 500000) -> dict:
    rows = [plan_for_trade(trade) | {"strategy": trade.get("strategy"), "setup_type": trade.get("setup_type")} for trade in load_candidate_trades()]
    payload = {"schema_version": "v6.2", "initial_cash_krw": initial_cash_krw, "router_rows": rows, "real_order_enabled": False, "live_order_allowed": False}
    _write("docs/reports/latest_v62_strategy_router_summary.json", payload)
    _write("replay_store/v62/latest_v62_strategy_router_summary.json", payload)
    return payload


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
