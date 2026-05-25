from __future__ import annotations

import pandas as pd


def choose_v6_exit(frame: pd.DataFrame, setup: dict) -> dict:
    entry_time = setup.get("entry_time")
    future = frame
    if entry_time:
        future = frame[pd.to_datetime(frame["time"]) >= pd.Timestamp(entry_time)]
    if future is None or future.empty:
        return {"exit_price": float(setup["entry_price"]), "exit_time": str(entry_time or ""), "result": "TIME_EXIT"}
    stop = float(setup["stop_price"])
    target = float(setup["target_price"])
    for _, row in future.iterrows():
        if float(row["low"]) <= stop:
            return {"exit_price": stop, "exit_time": str(row["time"]), "result": "LOSS"}
        if float(row["high"]) >= target:
            return {"exit_price": target, "exit_time": str(row["time"]), "result": "WIN"}
    last = future.iloc[-1]
    close = float(last["close"])
    result = "BREAKEVEN" if abs(close - float(setup["entry_price"])) / setup["entry_price"] < 0.001 else "TIME_EXIT"
    return {"exit_price": close, "exit_time": str(last["time"]), "result": result}
