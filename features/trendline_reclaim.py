from __future__ import annotations

import pandas as pd


def fit_resistance_trendline(swing_highs) -> dict:
    points = list(swing_highs)[-4:]
    if len(points) < 2:
        return {"has_trendline": False, "slope": 0.0, "intercept": 0.0, "touch_count": len(points)}
    x1, y1 = points[0]
    x2, y2 = points[-1]
    slope = (float(y2) - float(y1)) / max(1, int(x2) - int(x1))
    return {"has_trendline": True, "slope": slope, "intercept": float(y2) - slope * int(x2), "touch_count": len(points)}


def fit_support_trendline(swing_lows) -> dict:
    return fit_resistance_trendline(swing_lows)


def detect_trendline_break_reclaim(frame: pd.DataFrame) -> dict:
    data = _normalize(frame)
    if len(data) < 12:
        return _empty()
    highs = _swing_points(data["high"].astype(float), mode="high")
    trend = fit_resistance_trendline(highs)
    current = float(data.iloc[-1]["close"])
    score = 0.0
    broken = False
    distance = 999.0
    if trend["has_trendline"]:
        line = trend["slope"] * (len(data) - 1) + trend["intercept"]
        distance = (current - line) / current * 100 if current else 999.0
        broken = current >= line
        score += 60 if broken else max(0.0, 35 + distance)
        if trend["slope"] <= 0:
            score += 20
    return {"resistance_trendline_broken": bool(broken), "support_trendline_bounce": False, "distance_to_trendline_pct": float(distance), "trendline_score": float(max(0.0, min(100.0, score))), "warnings": []}


def detect_trendline_bounce(frame: pd.DataFrame) -> dict:
    data = _normalize(frame)
    if len(data) < 12:
        return _empty()
    lows = _swing_points(data["low"].astype(float), mode="low")
    trend = fit_support_trendline(lows)
    current = float(data.iloc[-1]["close"])
    low = float(data.iloc[-1]["low"])
    score = 0.0
    bounced = False
    distance = 999.0
    if trend["has_trendline"]:
        line = trend["slope"] * (len(data) - 1) + trend["intercept"]
        distance = abs(low - line) / current * 100 if current else 999.0
        bounced = low <= line * 1.005 and current >= line
        score += 60 if bounced else max(0.0, 45 - distance * 10)
        if trend["touch_count"] >= 3:
            score += 20
    return {"resistance_trendline_broken": False, "support_trendline_bounce": bool(bounced), "distance_to_trendline_pct": float(distance), "trendline_score": float(max(0.0, min(100.0, score))), "warnings": []}


def _swing_points(series: pd.Series, mode: str) -> list[tuple[int, float]]:
    points = []
    values = series.tolist()
    for idx in range(2, len(values) - 2):
        window = values[idx - 2 : idx + 3]
        if mode == "high" and values[idx] == max(window):
            points.append((idx, values[idx]))
        if mode == "low" and values[idx] == min(window):
            points.append((idx, values[idx]))
    return points


def _empty() -> dict:
    return {"resistance_trendline_broken": False, "support_trendline_bounce": False, "distance_to_trendline_pct": 999.0, "trendline_score": 0.0, "warnings": ["insufficient_data"]}


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
