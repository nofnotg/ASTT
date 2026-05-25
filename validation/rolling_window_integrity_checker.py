from __future__ import annotations

from typing import Any


def check_rolling_window_integrity(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    checked = 0
    for scenario in scenarios:
        for idx, trade in enumerate(scenario.get("annotated_trade_sample", [])):
            checked += 1
            if int(trade.get("rolling_trades_used", 0)) > idx:
                failures.append({"scenario": scenario.get("scenario"), "trade_id": trade.get("trade_id"), "reason": "rolling window includes current/future trade"})
    return {"check": "rolling_window_check", "status": "PASS" if not failures else "FAIL", "checked": checked, "failures": failures}
