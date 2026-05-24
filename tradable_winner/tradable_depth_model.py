from __future__ import annotations


def calculate_orderbook_depth_krw(orderbook: dict, levels: int = 3) -> dict:
    units = orderbook.get("units") or orderbook.get("orderbook_units") or []
    ask_depth = 0.0
    bid_depth = 0.0
    for unit in units[:levels]:
        ask_depth += float(unit.get("ask_price", 0.0) or 0.0) * float(unit.get("ask_size", 0.0) or 0.0)
        bid_depth += float(unit.get("bid_price", 0.0) or 0.0) * float(unit.get("bid_size", 0.0) or 0.0)
    return {"ask_depth_krw": ask_depth, "bid_depth_krw": bid_depth, "depth_krw": min(ask_depth, bid_depth)}


def is_tradable_depth(orderbook: dict, required_krw: float, levels: int = 3) -> dict:
    depth = calculate_orderbook_depth_krw(orderbook, levels=levels)
    return {
        **depth,
        "required_krw": required_krw,
        "tradable": depth["depth_krw"] >= required_krw,
        "depth_sufficiency_ratio": depth["depth_krw"] / required_krw if required_krw else 0.0,
    }
