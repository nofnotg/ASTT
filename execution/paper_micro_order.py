from __future__ import annotations


def build_paper_micro_order(market: str, side: str, price: float, order_krw: float, reason: list[str] | None = None) -> dict:
    return {"market": market, "side": side, "price": float(price), "order_krw": float(order_krw), "mode": "PAPER_MICRO", "real_order": False, "reason": reason or []}
