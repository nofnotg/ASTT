from __future__ import annotations

import hashlib
import pandas as pd

from features.zone_strength import compute_zone_strength


def detect_supply_demand_zones(frame, timeframe: str, as_of_time=None, min_bars: int = 20, max_atr_width: float = 3.0, volume_multiplier: float = 1.5) -> list[dict]:
    data = _as_of(_normalize(frame), as_of_time)
    if len(data) < min_bars:
        return []
    zones: list[dict] = []
    step = max(5, min_bars // 2)
    for start in range(max(0, len(data) - 240), len(data) - min_bars + 1, step):
        window = data.iloc[start : start + min_bars].copy()
        price = float(window["close"].iloc[-1])
        body_low = window[["open", "close"]].astype(float).min(axis=1)
        body_high = window[["open", "close"]].astype(float).max(axis=1)
        zone_low = float(body_low.quantile(0.20))
        zone_high = float(body_high.quantile(0.80))
        if zone_high <= zone_low or not price:
            continue
        width_pct = (zone_high - zone_low) / price * 100
        if width_pct > max_atr_width:
            continue
        volume = window["volume"].astype(float)
        volume_score = min(20.0, float(volume.mean() / max(1e-9, data["volume"].astype(float).tail(240).mean())) * 10)
        touch_score = min(15.0, float(((window["low"].astype(float) <= zone_high) & (window["high"].astype(float) >= zone_low)).sum()) / min_bars * 15)
        reaction = _reaction_score(data, start + min_bars, zone_low, zone_high)
        recency = max(0.0, 10.0 - (len(data) - (start + min_bars)) / 30)
        metrics = {"duration_bars": min_bars, "body_overlap_score": 18.0, "volume_score": volume_score, "touch_score": touch_score, "reaction_score": reaction, "recency_score": recency, "zone_width_pct": width_pct}
        strength = compute_zone_strength(metrics)["strength"]
        zone_type = "DEMAND" if price >= zone_high else "SUPPLY" if price <= zone_low else "RANGE"
        zone_id = hashlib.md5(f"{timeframe}:{zone_low:.8f}:{zone_high:.8f}:{start}".encode()).hexdigest()[:12]
        zones.append({"zone_id": zone_id, "timeframe": timeframe, "zone_low": zone_low, "zone_high": zone_high, "zone_mid": (zone_low + zone_high) / 2, "zone_width_pct": width_pct, "zone_type": zone_type, "strength": strength, "volume_score": volume_score, "body_overlap_score": 18.0, "touch_score": touch_score, "reaction_score": reaction, "recency_score": recency, "start_time": str(window.iloc[0].get("time", "")), "end_time": str(window.iloc[-1].get("time", "")), "source": "body_cluster"})
    return _merge_zones(sorted(zones, key=lambda z: z["strength"], reverse=True))[:20]


def _reaction_score(data: pd.DataFrame, idx: int, low: float, high: float) -> float:
    if idx >= len(data):
        return 0.0
    future = data.iloc[idx : min(len(data), idx + 12)]
    if future.empty:
        return 0.0
    move_up = (float(future["high"].max()) - high) / high * 100 if high else 0.0
    move_down = (low - float(future["low"].min())) / low * 100 if low else 0.0
    return min(15.0, max(move_up, move_down) * 5)


def _merge_zones(zones: list[dict]) -> list[dict]:
    merged: list[dict] = []
    for zone in zones:
        if any(_overlap(zone, item) for item in merged):
            continue
        merged.append(zone)
    return merged


def _overlap(a: dict, b: dict) -> bool:
    return max(a["zone_low"], b["zone_low"]) <= min(a["zone_high"], b["zone_high"])


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
