from __future__ import annotations


def build_tradable_momentum_features(snapshot: dict) -> dict:
    return {
        "price_change_180s_pct": float(snapshot.get("price_change_180s_pct", snapshot.get("price_change_60s_pct", 0.0)) or 0.0),
        "market_breadth_up_ratio": float(snapshot.get("market_breadth_up_ratio", 0.0) or 0.0),
        "btc_5m_change_pct": float(snapshot.get("btc_5m_change_pct", 0.0) or 0.0),
    }
