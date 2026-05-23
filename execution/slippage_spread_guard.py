from __future__ import annotations


def estimate_micro_execution_cost(entry_price, best_ask, best_bid, order_krw, orderbook_units=None, expected_target_pct: float = 0.6) -> dict:
    entry = float(entry_price or 0.0)
    ask = float(best_ask or 0.0)
    bid = float(best_bid or 0.0)
    mid = (ask + bid) / 2 if ask and bid else entry
    spread_pct = (ask - bid) / mid * 100 if mid else 999.0
    estimated_slippage_pct = _estimate_slippage(order_krw, orderbook_units)
    total = max(0.0, spread_pct) + estimated_slippage_pct
    warnings = []
    tradable = True
    if total >= expected_target_pct * 0.3:
        tradable = False
        warnings.append("cost_too_high_vs_target")
    return {"spread_pct": spread_pct, "estimated_slippage_pct": estimated_slippage_pct, "estimated_total_cost_pct": total, "tradable": tradable, "warnings": warnings}


def _estimate_slippage(order_krw: float, units) -> float:
    if not units:
        return 0.05
    remaining = float(order_krw)
    weighted = 0.0
    first_price = float(units[0].get("ask_price", 0.0)) or 1.0
    for unit in units:
        price = float(unit.get("ask_price", first_price))
        size_krw = price * float(unit.get("ask_size", 0.0))
        take = min(remaining, size_krw)
        weighted += take * ((price - first_price) / first_price * 100)
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        weighted += remaining * 0.15
    return weighted / max(order_krw, 1.0)
