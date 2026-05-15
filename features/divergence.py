from __future__ import annotations

import pandas as pd


def find_swing_lows(frame: pd.DataFrame, left: int = 3, right: int = 3) -> list[dict]:
    data = _normalize(frame)
    swings: list[dict] = []
    if data.empty or len(data) < left + right + 1:
        return swings
    for idx in range(left, len(data) - right):
        window = data.iloc[idx - left : idx + right + 1]
        low = float(data.iloc[idx]["low"])
        if low <= float(window["low"].min()):
            swings.append({"index": idx, "time": data.iloc[idx].get("time", idx), "low": low})
    return swings


def find_fear_peaks(frame: pd.DataFrame, left: int = 3, right: int = 3, column: str = "fear_score") -> list[dict]:
    data = _normalize(frame)
    peaks: list[dict] = []
    if data.empty or column not in data or len(data) < left + right + 1:
        return peaks
    for idx in range(left, len(data) - right):
        window = data.iloc[idx - left : idx + right + 1]
        score = float(data.iloc[idx][column])
        if score >= float(window[column].max()):
            peaks.append({"index": idx, "time": data.iloc[idx].get("time", idx), "fear": score})
    return peaks


def detect_bullish_fear_divergence(
    frame: pd.DataFrame,
    min_price_lower_low_pct: float = 0.3,
    max_fear_peak_ratio: float = 0.9,
    left: int = 3,
    right: int = 3,
) -> dict:
    data = _normalize(frame)
    lows = find_swing_lows(data, left, right)
    peaks = find_fear_peaks(data, left, right)
    base = {
        "has_bullish_fear_divergence": False,
        "price_low_1": 0.0,
        "price_low_2": 0.0,
        "fear_peak_1": 0.0,
        "fear_peak_2": 0.0,
        "price_lower_low_pct": 0.0,
        "fear_peak_ratio": 0.0,
        "divergence_strength": 0.0,
    }
    if len(lows) < 2 or len(peaks) < 2:
        return base
    low_1, low_2 = lows[-2], lows[-1]
    peak_1 = _nearest_prior_peak(peaks, low_1["index"]) or _local_fear_peak(data, low_1["index"], left + right + 1)
    peak_2 = _nearest_prior_peak(peaks, low_2["index"]) or _local_fear_peak(data, low_2["index"], left + right + 1)
    if not peak_1 or not peak_2:
        return base
    price_lower_low_pct = (low_1["low"] - low_2["low"]) / low_1["low"] * 100 if low_1["low"] else 0.0
    fear_peak_ratio = peak_2["fear"] / peak_1["fear"] if peak_1["fear"] else 1.0
    has = low_2["low"] < low_1["low"] and price_lower_low_pct >= min_price_lower_low_pct and fear_peak_ratio <= max_fear_peak_ratio
    strength = 0.0
    if has:
        price_component = min(price_lower_low_pct / 1.5, 1.0) * 45
        fear_component = min((1.0 - fear_peak_ratio) / 0.35, 1.0) * 55
        strength = max(0.0, min(100.0, price_component + fear_component))
    return {
        "has_bullish_fear_divergence": bool(has),
        "price_low_1": float(low_1["low"]),
        "price_low_2": float(low_2["low"]),
        "fear_peak_1": float(peak_1["fear"]),
        "fear_peak_2": float(peak_2["fear"]),
        "price_lower_low_pct": float(price_lower_low_pct),
        "fear_peak_ratio": float(fear_peak_ratio),
        "divergence_strength": float(strength),
    }


def _nearest_prior_peak(peaks: list[dict], index: int) -> dict | None:
    prior = [peak for peak in peaks if peak["index"] <= index]
    return prior[-1] if prior else None


def _local_fear_peak(data: pd.DataFrame, index: int, radius: int) -> dict | None:
    if "fear_score" not in data or data.empty:
        return None
    start = max(0, index - radius)
    end = min(len(data), index + radius + 1)
    scoped = data.iloc[start:end]
    if scoped.empty:
        return None
    local_idx = int(scoped["fear_score"].astype(float).idxmax())
    return {"index": local_idx, "time": data.iloc[local_idx].get("time", local_idx), "fear": float(data.iloc[local_idx]["fear_score"])}


def _normalize(frame: pd.DataFrame) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    data = frame.copy()
    if "candle_time_kst" in data and "time" not in data:
        data = data.rename(columns={"candle_time_kst": "time"})
    return data.reset_index(drop=True)
