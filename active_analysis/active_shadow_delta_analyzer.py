from __future__ import annotations


def analyze_active_shadow_delta(backfill: dict) -> dict:
    active = backfill.get("active_route")
    rows = backfill.get("routes", [])
    active_row = next((row for row in rows if row.get("scenario") == active), {})
    best_shadow = max([row for row in rows if row.get("scenario") != active], key=lambda row: float(row.get("return_pct", -999.0) or -999.0), default={})
    return {
        "active_route": active,
        "active_return_pct": active_row.get("return_pct"),
        "best_shadow": best_shadow.get("scenario"),
        "best_shadow_return_pct": best_shadow.get("return_pct"),
        "shadow_outperforming": bool(best_shadow and float(best_shadow.get("return_pct", -999.0) or -999.0) > float(active_row.get("return_pct", -999.0) or -999.0)),
    }
