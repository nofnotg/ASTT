from __future__ import annotations


def is_micro_noise(micro_signal: dict, min_volume_10s: float = 0.0) -> dict:
    warnings = []
    noisy = False
    if micro_signal.get("volume_10s", 0.0) <= min_volume_10s:
        noisy = True
        warnings.append("low_micro_volume")
    if abs(micro_signal.get("price_change_5s_pct", 0.0)) < 0.01:
        warnings.append("flat_micro_price")
    return {"is_noise": noisy, "warnings": warnings}
