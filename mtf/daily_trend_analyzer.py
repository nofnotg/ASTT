from __future__ import annotations

from mtf.weekly_trend_analyzer import _trend


def analyze_daily_trend(frame):
    return _trend(frame, "daily_trend")
