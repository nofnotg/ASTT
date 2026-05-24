from __future__ import annotations


def compute_effective_cost(snapshot: dict, fee_pct: float = 0.05, slippage_pct: float = 0.05) -> dict:
    spread_pct = float(snapshot.get("spread_pct", 999.0))
    cost_pct = fee_pct + slippage_pct + max(0.0, spread_pct / 2)
    return {"spread_pct": spread_pct, "estimated_cost_pct": cost_pct, "cost_ok": cost_pct <= 0.25}
