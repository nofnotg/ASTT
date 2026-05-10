from __future__ import annotations

import pandas as pd


def calculate_regime(btc_df: pd.DataFrame, market_tickers: list[dict] | None = None) -> dict:
    if btc_df is None or btc_df.empty or len(btc_df) < 2:
        return {"state": "neutral", "score": 50, "warning": "insufficient BTC data"}
    btc_return = (float(btc_df["close"].iloc[-1]) / float(btc_df["close"].iloc[0]) - 1) * 100
    rising_ratio = 0.5
    if market_tickers:
        changes = [item.get("signed_change_rate", 0) for item in market_tickers]
        rising_ratio = sum(1 for item in changes if item > 0) / len(changes) if changes else 0.5
    if btc_return <= -1.5 or rising_ratio < 0.35:
        state, score = "bearish", 30
    elif btc_return >= 0.5 and rising_ratio > 0.55:
        state, score = "bullish", 75
    else:
        state, score = "neutral", 55
    return {"state": state, "score": score, "btc_return_pct": btc_return, "rising_ratio": rising_ratio}

