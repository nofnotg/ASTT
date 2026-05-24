from __future__ import annotations


def execute_timing_entry(state: dict, entry_window: dict, initial_cash_krw: float = 500000) -> dict:
    allowed = (
        state.get("state") == "CONFIRMED"
        and bool(entry_window)
        and entry_window.get("effective_return_pct", 0) > 0
        and entry_window.get("tradable_with_500k")
    )
    if not allowed:
        return {
            "paper_entered": False,
            "real_order_enabled": False,
            "included_in_live_readiness": False,
            "reason": "CONFIRMED_ENTRY_WINDOW_REQUIRED",
        }
    return {
        "entry_state": "CONFIRMED",
        "paper_entered": True,
        "entry_time_ms": entry_window["start_ms"],
        "entry_price": entry_window["entry_price"],
        "allocated_krw": min(initial_cash_krw, initial_cash_krw * 0.3),
        "real_order_enabled": False,
        "included_in_live_readiness": False,
    }
