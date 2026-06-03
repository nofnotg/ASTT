from __future__ import annotations


def analyze_candidate_to_ledger(forward_events: list[dict], paper_trades: list[dict]) -> dict:
    enter_count = len([event for event in forward_events if event.get("entry_decision") == "ENTER"])
    return {
        "candidate_count": len(forward_events),
        "forward_enter_count": enter_count,
        "paper_trade_count": len(paper_trades),
        "ledger_gap": bool(forward_events and enter_count == 0),
        "interpretation": "forward 후보는 있으나 ledger 체결은 없습니다." if forward_events and enter_count == 0 else "ledger linkage requires more data",
    }
