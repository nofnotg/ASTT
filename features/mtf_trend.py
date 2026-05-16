from __future__ import annotations

import pandas as pd

from features.body_zone import body_zone_summary


def compute_weekly_bias(weekly_frame: pd.DataFrame, daily_frame: pd.DataFrame | None = None) -> dict:
    data = _normalize(weekly_frame)
    if len(data) < 4:
        return _result("weekly_bias_score", 0.0, "BEARISH", ["insufficient_weekly_data"], [])
    close = data["close"].astype(float)
    low = data["low"].astype(float)
    current = float(close.iloc[-1])
    ma20 = float(close.rolling(20, min_periods=2).mean().iloc[-1])
    recent_lows = low.tail(4).tolist()
    higher_lows = len(recent_lows) >= 3 and recent_lows[-1] >= min(recent_lows[:-1])
    decline_slowing = close.pct_change().tail(4).mean() >= close.pct_change().tail(8).mean()
    body = body_zone_summary(data, current)
    score = 0.0
    reasons: list[str] = []
    if higher_lows:
        score += 20
        reasons.append("weekly_higher_lows")
    if ma20 and current >= ma20 * 0.98:
        score += 15
        reasons.append("weekly_ma20_near_or_reclaimed")
    if body["body_zone_score"] >= 40:
        score += 20
        reasons.append("weekly_body_zone_reclaimed")
    if decline_slowing:
        score += 15
        reasons.append("weekly_decline_slowing")
    if body["target_space_pct"] >= 1.5:
        score += 15
        reasons.append("weekly_target_space")
    score += 15
    state = "BULLISH" if score >= 75 else "RECOVERING" if score >= 60 else "NEUTRAL" if score >= 50 else "BEARISH"
    return {
        "weekly_bias_score": float(max(0.0, min(100.0, score))),
        "weekly_state": state,
        "higher_lows": bool(higher_lows),
        "ma20_reclaimed": bool(current >= ma20 if ma20 else False),
        "body_zone_reclaimed": bool(body["body_zone_score"] >= 40),
        "target_space_pct": float(body["target_space_pct"]),
        "reasons": reasons,
        "warnings": [],
    }


def compute_daily_structure(daily_frame: pd.DataFrame, body_zones: list[dict] | None = None) -> dict:
    data = _normalize(daily_frame)
    if len(data) < 20:
        return _result("daily_structure_score", 0.0, "BREAKDOWN", ["insufficient_daily_data"], [])
    close = data["close"].astype(float)
    low = data["low"].astype(float)
    volume = data["volume"].astype(float)
    current = float(close.iloc[-1])
    ma20 = float(close.rolling(20, min_periods=5).mean().iloc[-1])
    ma30 = float(close.rolling(30, min_periods=5).mean().iloc[-1])
    ma60 = float(close.rolling(60, min_periods=5).mean().iloc[-1])
    body = body_zone_summary(data, current)
    support_touched = body["distance_to_support_pct"] <= 1.0 or min(abs(current - ma20), abs(current - ma30)) / current * 100 <= 1.0
    support_held = current >= min(ma20, ma30) * 0.985
    rs_flip = body["body_zone_score"] >= 40 and support_held
    higher_low = float(low.iloc[-1]) >= float(low.tail(10).min()) * 0.995
    volume_dry = float(volume.tail(3).mean()) <= float(volume.tail(20).mean()) * 1.2
    rebound_volume = float(volume.tail(2).mean()) >= float(volume.tail(10).mean()) * 0.9
    score = 0.0
    if current >= ma20 * 0.98 or current >= ma30 * 0.98 or current >= ma60 * 0.98:
        score += 20
    if rs_flip:
        score += 20
    if body["body_zone_score"] >= 40:
        score += 20
    if support_held or higher_low:
        score += 15
    if volume_dry:
        score += 10
    if rebound_volume:
        score += 10
    if body["target_space_pct"] >= 0.8:
        score += 5
    state = "UPTREND_PULLBACK" if score >= 75 else "SUPPORT_RETEST" if score >= 60 else "RECLAIM" if score >= 50 else "RANGE" if support_held else "BREAKDOWN"
    return {
        "daily_structure_score": float(max(0.0, min(100.0, score))),
        "daily_state": state,
        "support_touched": bool(support_touched),
        "support_held": bool(support_held),
        "rs_flip_candidate": bool(rs_flip),
        "target_space_pct": float(body["target_space_pct"]),
        "reasons": [state.lower()],
        "warnings": [],
    }


def compute_h4_flow(h4_frame: pd.DataFrame, body_zones: list[dict] | None = None) -> dict:
    data = _normalize(h4_frame)
    if len(data) < 20:
        return _result("h4_flow_score", 0.0, "BREAKDOWN", ["insufficient_h4_data"], [])
    close = data["close"].astype(float)
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    current = float(close.iloc[-1])
    ma20 = float(close.rolling(20, min_periods=5).mean().iloc[-1])
    ma30 = float(close.rolling(30, min_periods=5).mean().iloc[-1])
    middle = float(close.rolling(20, min_periods=5).mean().iloc[-1])
    trendline_broken = current >= float(high.tail(8).max()) * 0.995
    ma_reclaimed = current >= ma20 or current >= ma30
    higher_high_low = float(high.iloc[-1]) >= float(high.tail(8).median()) and float(low.iloc[-1]) >= float(low.tail(8).min()) * 0.995
    body = body_zone_summary(data, current)
    score = 0.0
    if trendline_broken:
        score += 20
    if ma_reclaimed:
        score += 20
    if current >= float(high.tail(12).max()) * 0.99:
        score += 15
    if higher_high_low:
        score += 15
    if current >= middle:
        score += 15
    if body["body_zone_score"] >= 40:
        score += 15
    state = "CONFIRMED_REVERSAL" if score >= 75 else "EARLY_RECLAIM" if score >= 60 else "PULLBACK" if score >= 45 else "WEAK" if ma_reclaimed else "BREAKDOWN"
    return {
        "h4_flow_score": float(max(0.0, min(100.0, score))),
        "h4_state": state,
        "trendline_broken": bool(trendline_broken),
        "ma_reclaimed": bool(ma_reclaimed),
        "higher_high_low": bool(higher_high_low),
        "reclaimed_body_zone": bool(body["body_zone_score"] >= 40),
        "reasons": [state.lower()],
        "warnings": [],
    }


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)


def _result(score_key: str, score: float, state: str, warnings: list[str], reasons: list[str]) -> dict:
    state_key = score_key.replace("_score", "_state")
    return {score_key: score, state_key: state, "reasons": reasons, "warnings": warnings}
