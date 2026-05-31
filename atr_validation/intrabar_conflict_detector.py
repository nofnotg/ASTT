from __future__ import annotations

from typing import Any


def detect_intrabar_conflict(row: dict[str, Any]) -> dict[str, Any]:
    entry = float(row.get("entry_price", 0.0) or 0.0)
    stop = float(row.get("stop_price", 0.0) or 0.0)
    target = float(row.get("target_price", 0.0) or 0.0)
    exit_price = float(row.get("exit_price", 0.0) or 0.0)
    has_stop_target = entry > 0 and stop > 0 and target > 0
    same_bar_unknown = has_stop_target and abs(target - stop) / entry < 0.08
    gap_risk = has_stop_target and exit_price > 0 and (exit_price < min(stop, target) or exit_price > max(stop, target))
    conflict = same_bar_unknown or gap_risk
    ctype = "UNKNOWN_INTRABAR_ORDER" if same_bar_unknown else "GAP_THROUGH_STOP" if gap_risk else "NO_CONFLICT"
    return {"bar_conflict": conflict, "conflict_type": ctype}
