from __future__ import annotations

import pandas as pd


def compute_weekly_power(weekly_completed_frame, current_week_frame, daily_frame, as_of_time=None) -> dict:
    completed = _as_of(_normalize(weekly_completed_frame), as_of_time)
    current = _as_of(_normalize(current_week_frame), as_of_time)
    daily = _as_of(_normalize(daily_frame), as_of_time)
    warnings = []
    if len(completed) < 2:
        warnings.append("insufficient_completed_weekly")
    last_completed = completed.iloc[-1] if not completed.empty else None
    current_row = current.iloc[-1] if not current.empty else (daily.iloc[-1] if not daily.empty else None)
    completed_bias = "NEUTRAL"
    if last_completed is not None:
        completed_bias = "BULL" if float(last_completed["close"]) >= float(last_completed["open"]) else "BEAR"
    candle = "DOJI"
    body_power = 0.0
    upper_risk = 0.0
    lower_support = 0.0
    if current_row is not None:
        o, h, l, c = [float(current_row[key]) for key in ["open", "high", "low", "close"]]
        rng = max(1e-9, h - l)
        body_power = abs(c - o) / rng * 100
        upper_risk = (h - max(o, c)) / rng * 100
        lower_support = (min(o, c) - l) / rng * 100
        candle = "BULL" if c > o else "BEAR" if c < o else "DOJI"
    score = 50.0
    if completed_bias == "BULL":
        score += 20
    elif completed_bias == "BEAR":
        score -= 20
    if candle == "BULL":
        score += 15
    elif candle == "BEAR":
        score -= 10
    if lower_support > upper_risk:
        score += 10
    if upper_risk > 45:
        score -= 15
    if score >= 75 and completed_bias == "BULL":
        state = "CONFIRMED_BULL"
    elif score >= 65:
        state = "CURRENT_BULL"
    elif completed_bias == "BULL" and candle == "BEAR":
        state = "BULL_PULLBACK"
    elif completed_bias == "BEAR" and candle == "BULL":
        state = "BEAR_RALLY"
    elif score < 35:
        state = "BREAKDOWN"
    else:
        state = "NEUTRAL"
    return {
        "weekly_power_score": max(0.0, min(100.0, score)),
        "weekly_state": state,
        "completed_week_bias": completed_bias,
        "current_week_candle": candle,
        "weekly_body_power": body_power,
        "weekly_upper_wick_risk": upper_risk,
        "weekly_lower_wick_support": lower_support,
        "warnings": warnings,
    }


def _as_of(frame: pd.DataFrame, as_of_time) -> pd.DataFrame:
    if frame.empty or as_of_time is None or "time" not in frame:
        return frame
    return frame[pd.to_datetime(frame["time"]) <= pd.Timestamp(as_of_time)].copy()


def _normalize(frame) -> pd.DataFrame:
    if frame is None or getattr(frame, "empty", True):
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
