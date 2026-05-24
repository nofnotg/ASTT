from __future__ import annotations

from features.effective_spread_cost_features import compute_effective_cost
from features.tradable_depth_features import compute_tradable_depth


def source_quality_pass(snapshot: dict, order_krw: float = 500000) -> dict:
    cost = compute_effective_cost(snapshot)
    depth = compute_tradable_depth(snapshot, order_krw)
    reject_reasons = []
    if not cost["cost_ok"]:
        reject_reasons.append("COST_TOO_HIGH")
    if not depth["tradable_with_500k"]:
        reject_reasons.append("INSUFFICIENT_DEPTH")
    if float(snapshot.get("spread_pct", 999.0)) > 0.20:
        reject_reasons.append("SPREAD_TOO_WIDE")
    return {**cost, **depth, "quality_pass": not reject_reasons, "reject_reasons": reject_reasons}
