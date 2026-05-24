from __future__ import annotations


def compute_market_breadth_proxy(snapshots: list[dict]) -> dict:
    if not snapshots:
        return {"market_breadth_up_ratio": 0.0}
    up = sum(1 for snapshot in snapshots if float(snapshot.get("price_change_60s_pct", 0.0)) > 0)
    return {"market_breadth_up_ratio": up / len(snapshots)}
