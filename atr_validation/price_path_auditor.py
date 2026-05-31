from __future__ import annotations

from typing import Any

from atr_validation.atr_precision_schema import ATRAuditConfig
from atr_validation.intrabar_conflict_detector import detect_intrabar_conflict


def build_price_path_rows(journal: list[dict[str, Any]], config: ATRAuditConfig = ATRAuditConfig()) -> list[dict[str, Any]]:
    rows = []
    for row in journal:
        conflict = detect_intrabar_conflict(row)
        entry = float(row.get("entry_price", 0.0) or 0.0)
        stop = float(row.get("stop_price", 0.0) or 0.0)
        target = float(row.get("target_price", 0.0) or 0.0)
        rows.append(
            {
                "trade_id": row.get("trade_id"),
                "market": row.get("market"),
                "entry_time": row.get("entry_time"),
                "exit_time": row.get("exit_time"),
                "atr_timeframe": config.atr_timeframe,
                "atr_period": config.atr_period,
                "atr_multiplier": config.atr_multiplier,
                **conflict,
                "conservative_exit_price": stop or min(entry, target),
                "optimistic_exit_price": target or max(entry, stop),
                "neutral_exit_price": (stop + target) / 2.0 if stop and target else entry,
                "decision": "REQUIRES_1M_REPLAY" if conflict["bar_conflict"] else "AMBIGUOUS",
            }
        )
    return rows
