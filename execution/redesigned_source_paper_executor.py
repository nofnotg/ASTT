from __future__ import annotations


def execute_redesigned_source_paper(candidate: dict, decision: str, order_krw: float = 500000) -> dict:
    if decision != "ENTER":
        return {"paper_trade_created": False, "included_in_pnl": False, "pnl_evaluable": False, "total_pnl_krw": None}
    return {
        "paper_trade_created": True,
        "included_in_pnl": True,
        "pnl_evaluable": True,
        "order_krw": order_krw,
        "total_pnl_krw": 0.0,
        "real_order_enabled": False,
    }
