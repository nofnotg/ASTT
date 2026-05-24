from __future__ import annotations


def close_timing_position(entry: dict, exit_price: float | None = None) -> dict:
    if not entry.get("paper_entered"):
        return {"exit_summary": {}, "realistic_1_pnl_krw": 0.0, "realistic_1_return_pct": 0.0, "pnl_evaluable": False}
    entry_price = float(entry.get("entry_price", 0.0))
    exit_price = float(exit_price or entry_price)
    allocated = float(entry.get("allocated_krw", 0.0))
    ret = (exit_price - entry_price) / entry_price if entry_price else 0.0
    pnl = allocated * ret
    return {"exit_summary": {"exit_price": exit_price}, "realistic_1_pnl_krw": pnl, "realistic_1_return_pct": ret * 100, "pnl_evaluable": True}
