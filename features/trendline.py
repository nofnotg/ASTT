from __future__ import annotations

import pandas as pd

from features.divergence import find_swing_lows


def fit_support_trendline(swing_lows: list[dict]) -> dict:
    points = swing_lows[-4:]
    if len(points) < 2:
        return {"has_support_trendline": False, "trendline_slope": 0.0, "intercept": 0.0, "touch_count": len(points)}
    x1, y1 = float(points[0]["index"]), float(points[0]["low"])
    x2, y2 = float(points[-1]["index"]), float(points[-1]["low"])
    if x2 == x1:
        return {"has_support_trendline": False, "trendline_slope": 0.0, "intercept": 0.0, "touch_count": len(points)}
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return {"has_support_trendline": True, "trendline_slope": float(slope), "intercept": float(intercept), "touch_count": len(points)}


def detect_trendline_bounce(frame: pd.DataFrame, tolerance_pct: float = 0.5) -> dict:
    data = _normalize(frame)
    if data.empty:
        return _empty()
    swing_lows = find_swing_lows(data, left=2, right=2)
    line = fit_support_trendline(swing_lows)
    if not line["has_support_trendline"]:
        return _empty()
    idx = len(data) - 1
    trend_value = line["trendline_slope"] * idx + line["intercept"]
    current = data.iloc[-1]
    close = float(current["close"])
    low = float(current["low"])
    distance = (low - trend_value) / trend_value * 100 if trend_value else 999.0
    touch = abs(distance) <= tolerance_pct or (low <= trend_value and close >= trend_value)
    recovered = close >= trend_value
    score = 0.0
    if touch and recovered:
        score = 60.0
        score += min(line["touch_count"], 4) * 8
        if line["trendline_slope"] >= 0:
            score += 8
        elif abs(line["trendline_slope"]) / close > 0.002:
            score -= 15
    return {
        "has_support_trendline": True,
        "trendline_slope": float(line["trendline_slope"]),
        "distance_to_trendline_pct": float(distance),
        "trendline_bounce": bool(touch and recovered),
        "trendline_score": max(0.0, min(100.0, score)),
        "trendline_touch_count": int(line["touch_count"]),
    }


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)


def _empty() -> dict:
    return {"has_support_trendline": False, "trendline_slope": 0.0, "distance_to_trendline_pct": 999.0, "trendline_bounce": False, "trendline_score": 0.0, "trendline_touch_count": 0}
