from __future__ import annotations


def btc_context_allows_momentum(snapshot: dict, max_btc_drop_pct: float = -0.3) -> bool:
    return float(snapshot.get("btc_5m_change_pct", 0.0) or 0.0) >= max_btc_drop_pct
