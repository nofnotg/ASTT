from __future__ import annotations


def compare_metrics(champion: dict, challenger: dict) -> dict:
    return {
        "pnl_delta_pct": float(challenger.get("total_pnl_pct", 0)) - float(champion.get("total_pnl_pct", 0)),
        "win_rate_delta": float(challenger.get("win_rate", 0)) - float(champion.get("win_rate", 0)),
        "recommendation": "PROMOTE_CANDIDATE" if float(challenger.get("total_pnl_pct", 0)) > float(champion.get("total_pnl_pct", 0)) else "KEEP_CHAMPION",
    }

