from __future__ import annotations


def execute_tradable_source_paper(candidate: dict, decision: str, initial_cash_krw: float = 500000) -> dict:
    if decision != "ENTER":
        return {"paper_trade_created": False, "included_in_pnl": False, "position_created": False, "real_order_enabled": False}
    return {
        "paper_trade_created": True,
        "included_in_pnl": True,
        "position_created": True,
        "source": candidate.get("candidate_source"),
        "order_krw": min(initial_cash_krw, initial_cash_krw * 0.3),
        "total_pnl_krw": 0.0,
        "real_order_enabled": False,
    }
