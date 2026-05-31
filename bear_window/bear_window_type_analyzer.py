from __future__ import annotations

from collections import defaultdict
from typing import Any


def type_summary(window_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in window_rows:
        groups[str(row.get("window_type", "UNKNOWN"))].append(row)
    out = []
    for window_type, rows in sorted(groups.items()):
        best_counts: dict[str, int] = {}
        for row in rows:
            best_counts[str(row.get("best_route"))] = best_counts.get(str(row.get("best_route")), 0) + 1
        best = max(best_counts, key=best_counts.get) if best_counts else "UNKNOWN"
        out.append(
            {
                "window_type": window_type,
                "best_scenario": best,
                "avg_return": sum(float(row.get("best_return", row.get("best_return_pct", 0.0))) for row in rows) / len(rows),
                "avg_mdd": sum(float(row.get("mdd", row.get("best_mdd_pct", 0.0))) for row in rows) / len(rows),
                "recommended_action": _action(window_type, best),
            }
        )
    return out


def _action(window_type: str, best: str) -> str:
    if window_type == "RECOVERY_WINDOW":
        return "Bear Bounce remains research only; prefer validated shadow route."
    if window_type == "DRAWDOWN_WINDOW":
        return "Use defensive sizing shadow candidate; no active auto-switch."
    if window_type == "BTC_LED_ALT_WEAK_WINDOW":
        return "Cap non-PlanA risk; validate dominance risk without hard block."
    return f"Prefer {best} as shadow observation route."
