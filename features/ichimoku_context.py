from __future__ import annotations

import pandas as pd


def compute_ichimoku_context(frame: pd.DataFrame) -> dict:
    data = _normalize(frame)
    if len(data) < 52:
        return {"ichimoku_score": 0.0, "cloud_state": "BELOW_CLOUD", "tenkan_above_kijun": False, "kijun_slope": "FLAT", "long_allowed": False, "reasons": [], "warnings": ["insufficient_ichimoku_data"]}
    high = data["high"].astype(float)
    low = data["low"].astype(float)
    close = data["close"].astype(float)
    tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
    kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = (tenkan + kijun) / 2
    span_b = (high.rolling(52).max() + low.rolling(52).min()) / 2
    current = float(close.iloc[-1])
    cloud_top = float(max(span_a.iloc[-1], span_b.iloc[-1]))
    cloud_bottom = float(min(span_a.iloc[-1], span_b.iloc[-1]))
    if current > cloud_top:
        cloud_state = "ABOVE_CLOUD"
    elif current >= cloud_bottom:
        cloud_state = "INSIDE_CLOUD"
    else:
        cloud_state = "BELOW_CLOUD"
    tenkan_above = bool(float(tenkan.iloc[-1]) > float(kijun.iloc[-1]))
    kijun_slope_value = float(kijun.iloc[-1]) - float(kijun.iloc[-5])
    kijun_slope = "UP" if kijun_slope_value > 0 else "DOWN" if kijun_slope_value < 0 else "FLAT"
    score = 0.0
    score += 45 if cloud_state == "ABOVE_CLOUD" else 25 if cloud_state == "INSIDE_CLOUD" else 0
    if tenkan_above:
        score += 25
    if kijun_slope == "UP":
        score += 20
    elif kijun_slope == "FLAT":
        score += 10
    long_allowed = cloud_state != "BELOW_CLOUD" and score >= 45
    return {"ichimoku_score": float(min(100.0, score)), "cloud_state": cloud_state, "tenkan_above_kijun": tenkan_above, "kijun_slope": kijun_slope, "long_allowed": bool(long_allowed), "reasons": [cloud_state.lower()], "warnings": []}


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
