from __future__ import annotations

from pathlib import Path
from typing import Any

from scenario_telemetry.v688_common import ACTIVE_ROUTE, daily_rows_from_backfill, load_context, safe_status, write_html, write_json


def build_profit_giveback_analysis(
    initial_cash_krw: float = 500000.0,
    use_available_history: bool = True,
    reports_dir: str | Path = "docs/reports",
    data_dir: str | Path = "data/paper",
) -> dict[str, Any]:
    ctx = load_context(reports_dir, data_dir)
    rows = daily_rows_from_backfill(ctx["backfill"], ctx["backfill"].get("active_route") or ACTIVE_ROUTE)
    ordered = sorted(rows, key=lambda row: str(row.get("date", "")))
    givebacks = []
    for idx, row in enumerate(ordered):
        pnl = float(row.get("realized_pnl_krw", 0.0) or 0.0)
        if pnl <= 0:
            continue
        windows = {days: sum(float(r.get("realized_pnl_krw", 0.0) or 0.0) for r in ordered[idx + 1 : idx + 1 + days]) for days in (1, 3, 5)}
        givebacks.append(
            {
                "scenario_id": row.get("scenario_id"),
                "profit_date": row.get("date"),
                "profit_day_pnl": pnl,
                "next_1d_pnl": windows[1],
                "next_3d_pnl": windows[3],
                "next_5d_pnl": windows[5],
                "giveback_ratio_1d": _ratio(pnl, windows[1]),
                "giveback_ratio_3d": _ratio(pnl, windows[3]),
                "giveback_ratio_5d": _ratio(pnl, windows[5]),
                "market_state_after_profit": ordered[idx + 1].get("market_state") if idx + 1 < len(ordered) else None,
                "route_after_profit": row.get("scenario_id"),
                "whether_guard_triggered": False,
                "recommendation": _recommendation(pnl, windows[3]),
            }
        )
    payload = {
        "schema_version": "v688_profit_giveback_v1",
        "rows": givebacks,
        "row_count": len(givebacks),
        "profit_lock_candidate": [row for row in givebacks if row.get("giveback_ratio_3d", 0.0) >= 0.7],
        "next_day_size_reduction_candidate": [row for row in givebacks if row.get("giveback_ratio_1d", 0.0) >= 0.5],
        "decision": "PROFIT_LOCK_REVIEW" if any(row.get("giveback_ratio_3d", 0.0) >= 0.7 for row in givebacks) else "NO_CHANGE_REQUIRED",
        **safe_status(),
    }
    reports = Path(reports_dir)
    write_json(reports / "latest_v688_profit_giveback_summary.json", payload)
    write_html(reports / "latest_v688_profit_giveback_report.html", "V6.8.8 Profit Giveback", [("Giveback Rows", givebacks), ("Summary", payload)])
    return payload


def _ratio(profit: float, next_pnl: float) -> float:
    return abs(min(next_pnl, 0.0)) / profit if profit > 0 else 0.0


def _recommendation(profit: float, next_3d: float) -> str:
    ratio = _ratio(profit, next_3d)
    if ratio >= 0.7:
        return "profit_lock_candidate"
    if ratio >= 0.5:
        return "next_day_size_reduction_candidate"
    return "no_change_required"
