from __future__ import annotations

import pandas as pd


def calculate_body_zones(df: pd.DataFrame, multiplier: float = 2.0, lookback: int = 20) -> dict:
    if df is None or df.empty or len(df) < 3:
        return {"zones": [], "warning": "insufficient candle data"}
    data = df.copy()
    data["volume_mean"] = data["volume"].rolling(lookback, min_periods=1).mean()
    data["is_heavy"] = data["volume"] >= data["volume_mean"] * multiplier
    data["body_low"] = data[["open", "close"]].min(axis=1)
    data["body_high"] = data[["open", "close"]].max(axis=1)
    heavy = data[data["is_heavy"]].tail(5)
    zones = []
    current = float(data["close"].iloc[-1])
    for _, row in heavy.iterrows():
        body_low = float(row["body_low"])
        body_high = float(row["body_high"])
        zones.append(
            {
                "body_low": body_low,
                "body_high": body_high,
                "distance_pct": ((current - body_high) / body_high * 100) if body_high else 0,
                "volume": float(row["volume"]),
            }
        )
    return {"zones": zones, "current_price": current}


def detect_rs_flip(df: pd.DataFrame, zone: dict | None = None) -> dict:
    if df is None or df.empty or len(df) < 2:
        return {"state": "FAILED", "warning": "insufficient candle data"}
    current = float(df["close"].iloc[-1])
    previous = float(df["close"].iloc[-2])
    high = float(zone["body_high"]) if zone else float(df["high"].rolling(20, min_periods=1).max().iloc[-2])
    if previous <= high < current:
        state = "BREAKOUT"
    elif current >= high * 0.995:
        state = "PRE_BREAKOUT"
    elif current >= high:
        state = "RETEST"
    else:
        state = "FAILED"
    return {"state": state, "reference_price": high, "current_price": current}


def target_space_pct(current_price: float, recent_high: float) -> float:
    if current_price <= 0:
        return 0.0
    return max(0.0, (recent_high - current_price) / current_price * 100)

