from __future__ import annotations

from typing import Any


def best_route(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return max(rows, key=lambda row: (float(row.get("window_return_pct", -999.0)), float(row.get("window_mdd_pct", -999.0))), default={})
