from __future__ import annotations


def build_tradable_spike_features(snapshot: dict) -> dict:
    return {
        "price_change_600s_pct": float(snapshot.get("price_change_600s_pct", snapshot.get("price_change_60s_pct", 0.0)) or 0.0),
        "volume_burst_60s_vs_600s": float(snapshot.get("volume_burst_60s_vs_600s", 0.0) or 0.0),
    }
