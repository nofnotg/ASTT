from __future__ import annotations


def plan_stop_target(entry_price: float, zone_low: float | None = None, rr: float = 1.8) -> dict:
    if entry_price <= 0:
        return {"stop_price": 0.0, "target_price": 0.0, "valid": False}
    stop = min(zone_low if zone_low else entry_price * 0.97, entry_price * 0.992)
    if stop <= 0 or stop >= entry_price:
        return {"stop_price": 0.0, "target_price": 0.0, "valid": False}
    target = entry_price + (entry_price - stop) * rr
    return {"stop_price": float(stop), "target_price": float(target), "valid": True}
