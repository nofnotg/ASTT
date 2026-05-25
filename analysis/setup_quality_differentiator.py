from __future__ import annotations


def differentiate_setup_quality(trades: list[dict]) -> dict:
    wins = [row for row in trades if row.get("pnl_krw", 0) > 0]
    losses = [row for row in trades if row.get("pnl_krw", 0) <= 0]
    return {"win_count": len(wins), "loss_count": len(losses), "quality_note": "Compare setup type, regime, and RR before forwarding."}
