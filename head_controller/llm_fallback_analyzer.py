from __future__ import annotations

from head_controller.head_controller_analyzer import analyze_head_controller_context


def fallback_head_controller_analysis(context: dict, reason: str = "FALLBACK") -> dict:
    result = analyze_head_controller_context(context)
    result["fallback_used"] = True
    result["fallback_reason"] = reason
    result["auto_apply_allowed"] = False
    result["live_order_allowed"] = False
    return result
