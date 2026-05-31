from __future__ import annotations

from typing import Any

from dominance_router.high_watermark_defense_analyzer import analyze_high_watermark


def build_v673_high_watermark_report(summary: dict[str, Any]) -> dict[str, Any]:
    journal = summary.get("router_journal", [])
    hwm = analyze_high_watermark(journal)
    return {
        "schema_version": "v673_high_watermark_v1",
        **hwm,
        "best_hwm_scenario": _best(summary.get("scenarios", [])),
        "real_order_enabled": False,
        "live_order_allowed": False,
        "auto_apply_allowed": False,
    }


def _best(rows: list[dict[str, Any]]) -> str | None:
    scored = [row for row in rows if row.get("final_equity_krw") is not None]
    if not scored:
        return None
    return max(scored, key=lambda row: float(row.get("return_mdd_ratio") or 0.0)).get("scenario")
