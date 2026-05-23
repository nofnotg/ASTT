from __future__ import annotations

import pandas as pd


def compute_micro_signal_features(second_candles, trade_ticks=None, orderbook_ticks=None, as_of_time=None) -> dict:
    frame = _as_frame(second_candles, as_of_time)
    if frame.empty:
        return _empty("NO_DATA")
    close = frame["close"].astype(float)
    volume = frame["volume"].astype(float) if "volume" in frame else pd.Series([0.0] * len(frame))
    latest = float(close.iloc[-1])
    features = {
        "price_change_3s_pct": _change(close, latest, 3),
        "price_change_5s_pct": _change(close, latest, 5),
        "price_change_10s_pct": _change(close, latest, 10),
        "volume_5s": float(volume.tail(5).sum()),
        "volume_10s": float(volume.tail(10).sum()),
        "buy_trade_ratio_5s": _buy_ratio(trade_ticks, as_of_time, 5),
        "buy_trade_ratio_10s": _buy_ratio(trade_ticks, as_of_time, 10),
        "warnings": [],
    }
    score = max(0.0, min(100.0, 50 + features["price_change_5s_pct"] * 120 + (features["buy_trade_ratio_5s"] - 0.5) * 60))
    features["micro_momentum_score"] = score
    features["micro_state"] = _state(features)
    return features


def _as_frame(data, as_of_time) -> pd.DataFrame:
    frame = data.copy() if isinstance(data, pd.DataFrame) else pd.DataFrame(data or [])
    if frame.empty:
        return frame
    frame["time"] = pd.to_datetime(frame.get("time", frame.get("candle_time_kst")), errors="coerce")
    if as_of_time is not None:
        frame = frame[frame["time"] <= pd.Timestamp(as_of_time)]
    return frame.sort_values("time")


def _change(close: pd.Series, latest: float, seconds: int) -> float:
    if len(close) <= seconds:
        return 0.0
    base = float(close.iloc[-seconds - 1])
    return (latest - base) / base * 100 if base else 0.0


def _buy_ratio(trade_ticks, as_of_time, seconds: int) -> float:
    ticks = pd.DataFrame(trade_ticks or [])
    if ticks.empty or "ask_bid" not in ticks:
        return 0.5
    if "trade_timestamp" in ticks:
        ticks["time"] = pd.to_datetime(ticks["trade_timestamp"], unit="ms", errors="coerce")
        if ticks["time"].isna().all():
            ticks["time"] = pd.to_datetime(ticks["trade_timestamp"], errors="coerce")
    elif "time" in ticks:
        ticks["time"] = pd.to_datetime(ticks["time"], errors="coerce")
    if as_of_time is not None and "time" in ticks:
        cutoff = pd.Timestamp(as_of_time) - pd.Timedelta(seconds=seconds)
        ticks = ticks[(ticks["time"] <= pd.Timestamp(as_of_time)) & (ticks["time"] >= cutoff)]
    if ticks.empty:
        return 0.5
    return float((ticks["ask_bid"].astype(str).str.upper() == "BID").mean())


def _state(features: dict) -> str:
    if features["price_change_5s_pct"] > 0.05 and features["buy_trade_ratio_5s"] >= 0.58:
        return "ACCELERATING"
    if features["price_change_5s_pct"] >= 0 and features["buy_trade_ratio_5s"] >= 0.5:
        return "STABLE"
    if features["price_change_5s_pct"] < -0.08:
        return "REVERSING"
    return "FADING"


def _empty(state: str) -> dict:
    return {"price_change_3s_pct": 0.0, "price_change_5s_pct": 0.0, "price_change_10s_pct": 0.0, "volume_5s": 0.0, "volume_10s": 0.0, "buy_trade_ratio_5s": 0.0, "buy_trade_ratio_10s": 0.0, "micro_momentum_score": 0.0, "micro_state": state, "warnings": ["micro_signal_no_data"]}
