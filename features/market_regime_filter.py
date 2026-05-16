from __future__ import annotations

import pandas as pd


def evaluate_market_regime(btc_frame: pd.DataFrame | None = None, market_frames: list[pd.DataFrame] | None = None) -> dict:
    warnings: list[str] = []
    btc_5m = _return_pct(btc_frame, 5)
    btc_15m = _return_pct(btc_frame, 15)
    breadth = _breadth(market_frames or [])
    score = 65.0
    if btc_5m <= -0.7:
        score -= 35
        warnings.append("btc_5m_shock")
    if btc_15m <= -1.2:
        score -= 35
        warnings.append("btc_15m_shock")
    if breadth <= 0.25:
        score -= 25
        warnings.append("weak_krw_breadth")
    if score <= 25:
        regime = "BTC_SHOCK" if "btc_5m_shock" in warnings or "btc_15m_shock" in warnings else "RISK_OFF"
    elif score < 50:
        regime = "RISK_OFF"
    elif score < 70:
        regime = "NEUTRAL"
    else:
        regime = "RISK_ON"
    return {"regime": regime, "regime_score": max(0.0, min(100.0, score)), "warnings": warnings, "long_allowed": regime not in {"BTC_SHOCK", "RISK_OFF"}}


def _return_pct(frame: pd.DataFrame | None, bars: int) -> float:
    if frame is None or frame.empty or len(frame) <= bars:
        return 0.0
    close = frame["close"].astype(float)
    start = float(close.iloc[-bars])
    end = float(close.iloc[-1])
    return (end - start) / start * 100 if start else 0.0


def _breadth(frames: list[pd.DataFrame]) -> float:
    if not frames:
        return 0.5
    up = 0
    total = 0
    for frame in frames:
        if frame is None or frame.empty or len(frame) < 2:
            continue
        total += 1
        if float(frame.iloc[-1]["close"]) >= float(frame.iloc[-2]["close"]):
            up += 1
    return up / total if total else 0.5
