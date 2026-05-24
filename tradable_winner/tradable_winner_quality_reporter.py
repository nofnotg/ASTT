from __future__ import annotations


def summarize_tradable_winner_quality(winners: list[dict]) -> dict:
    return {
        "tradable_winner_count": len(winners),
        "avg_effective_return_pct": sum(float(w.get("effective_return_pct", 0.0) or 0.0) for w in winners) / len(winners) if winners else 0.0,
        "tradable_with_500k_count": sum(1 for w in winners if w.get("tradable_with_500k")),
    }
