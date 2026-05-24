from __future__ import annotations


def compute_volume_acceleration(snapshot: dict) -> dict:
    ratio = float(snapshot.get("volume_burst_ratio_10s_vs_60s", 0.0))
    trade_accel = float(snapshot.get("trade_count_acceleration", 0.0))
    return {"volume_burst_ratio": ratio, "trade_count_acceleration": trade_accel, "volume_acceleration": ratio >= 1.2 or trade_accel >= 1.2}
