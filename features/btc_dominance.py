from __future__ import annotations

import pandas as pd


def compute_btc_dominance_regime(btc_frame, dominance_frame=None, krw_breadth=None, as_of_time=None) -> dict:
    btc = _as_of(_normalize(btc_frame), as_of_time)
    dom = _as_of(_normalize(dominance_frame), as_of_time) if dominance_frame is not None else pd.DataFrame()
    breadth = 0.5 if krw_breadth is None else float(krw_breadth)
    btc_5m = _ret(btc, 5)
    btc_15m = _ret(btc, 15)
    btc_1h = _ret(btc, 60)
    btc_4h = _ret(btc, 240)
    dom_1h = _ret(dom, 60, col="dominance") if not dom.empty and "dominance" in dom else None
    dom_4h = _ret(dom, 240, col="dominance") if not dom.empty and "dominance" in dom else None
    warnings = []
    if dom_1h is None:
        warnings.append("dominance_unavailable")
    risk_off = btc_5m <= -0.7 or btc_15m <= -1.2 or breadth <= 0.25
    if risk_off:
        regime = "RISK_OFF"
        mult = 0.0
    elif dom_1h is None:
        regime = "DOMINANCE_UNAVAILABLE"
        mult = 0.7
    elif btc_1h >= 0 and dom_1h <= 0 and breadth >= 0.5:
        regime = "ALT_RISK_ON"
        mult = 1.0
    elif btc_1h >= 0 and dom_1h > 0:
        regime = "BTC_LED"
        mult = 0.6
    else:
        regime = "UNCLEAR"
        mult = 0.4
    return {
        "btc_return_5m": btc_5m,
        "btc_return_15m": btc_15m,
        "btc_return_1h": btc_1h,
        "btc_return_4h": btc_4h,
        "dominance_change_1h": dom_1h,
        "dominance_change_4h": dom_4h,
        "krw_breadth": breadth,
        "alt_regime": regime,
        "alt_long_allowed": not risk_off and regime != "RISK_OFF",
        "position_size_multiplier": mult,
        "warnings": warnings,
    }


def _ret(frame: pd.DataFrame, bars: int, col: str = "close") -> float:
    if frame.empty or col not in frame or len(frame) <= bars:
        return 0.0
    start = float(frame[col].iloc[-bars])
    end = float(frame[col].iloc[-1])
    return (end - start) / start * 100 if start else 0.0


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
