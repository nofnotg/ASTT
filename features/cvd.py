from __future__ import annotations

import pandas as pd


def calculate_cvd(trades: pd.DataFrame) -> dict:
    if trades is None or trades.empty:
        return {"cvd": 0.0, "direction": "flat", "warning": "insufficient trade data"}
    data = trades.copy()
    if "ask_bid" not in data.columns or "trade_volume" not in data.columns:
        return {"cvd": 0.0, "direction": "flat", "warning": "missing ask_bid or trade_volume"}
    signed = data["trade_volume"].where(data["ask_bid"].str.upper() == "BID", -data["trade_volume"])
    cvd = float(signed.sum())
    direction = "up" if cvd > 0 else "down" if cvd < 0 else "flat"
    return {"cvd": cvd, "direction": direction}

