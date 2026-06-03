from __future__ import annotations


def classify_vpf(row: dict) -> dict:
    distance = float(row.get("vwap_distance_pct", 0.0) or 0.0)
    volume_z = float(row.get("volume_zscore", 0.0) or 0.0)
    body = float(row.get("candle_body_ratio", 0.0) or 0.0)
    close_loc = float(row.get("close_location_in_range", 0.5) or 0.5)
    chop = int(row.get("chop_cross_count", 0) or 0)
    dominance_risk = bool(row.get("dominance_risk", False))
    btc_unfavorable = bool(row.get("btc_trend_unfavorable", False))

    buy = 0.0
    sell = 0.0
    grey = 0.0
    buy += 1.0 if distance > 0 else 0.0
    buy += 1.0 if volume_z >= 1.0 else 0.0
    buy += 1.0 if body >= 0.4 else 0.0
    buy += 1.0 if close_loc >= 0.65 else 0.0
    buy += 1.0 if row.get("vwap_reclaim") or row.get("vwap_retest_hold") else 0.0
    buy -= 1.0 if dominance_risk or btc_unfavorable else 0.0

    sell += 1.0 if distance < 0 else 0.0
    sell += 1.0 if volume_z >= 1.0 else 0.0
    sell += 1.0 if body >= 0.4 else 0.0
    sell += 1.0 if close_loc <= 0.35 else 0.0
    sell += 1.0 if row.get("vwap_rejection") or row.get("vwap_retest_fail") else 0.0
    sell += 1.0 if dominance_risk or btc_unfavorable else 0.0

    grey += 1.0 if abs(distance) <= 0.25 else 0.0
    grey += 1.0 if volume_z < 0.8 else 0.0
    grey += 1.0 if body < 0.35 else 0.0
    grey += 1.0 if 0.35 < close_loc < 0.65 else 0.0
    grey += 1.0 if chop >= 3 else 0.0

    if grey >= 3.0:
        state = "GREY"
    elif buy > sell and buy >= 3.0:
        state = "GREEN"
    elif sell >= 3.0:
        state = "WHITE"
    else:
        state = "GREY"

    reason = "estimated_pressure_from_ohlcv_not_orderflow"
    return {
        **row,
        "vpf_state": state,
        "vpf_score": max(buy, sell, grey),
        "vpf_buy_pressure_score": buy,
        "vpf_sell_pressure_score": sell,
        "vpf_grey_score": grey,
        "vpf_reason": reason,
    }


def attach_vpf_pressure(rows: list[dict]) -> list[dict]:
    return [classify_vpf(row) for row in rows]
