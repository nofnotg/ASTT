from __future__ import annotations


def detect_btc_shock(btc_1m_change_pct: float, threshold_pct: float = 0.3) -> dict:
    return {"triggered": abs(btc_1m_change_pct) >= threshold_pct, "btc_1m_change_pct": btc_1m_change_pct, "threshold_pct": threshold_pct}


def detect_volume_spike(current_volume: float, baseline_volume: float, ratio_threshold: float = 2.0) -> dict:
    ratio = current_volume / baseline_volume if baseline_volume > 0 else 0.0
    return {"triggered": ratio >= ratio_threshold, "volume_ratio": ratio, "ratio_threshold": ratio_threshold}
