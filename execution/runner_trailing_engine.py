from __future__ import annotations

import pandas as pd


def evaluate_trailing_stop(
    post_entry_frame: pd.DataFrame,
    entry_price: float,
    stop_price: float,
    model: str,
    tp1_hit: bool = False,
) -> dict:
    if post_entry_frame is None or post_entry_frame.empty:
        return {"hit": False, "stop_price": float(stop_price), "hit_time": None, "reason": "NO_DATA"}
    peak = float(entry_price)
    trailing = float(stop_price)
    for row in post_entry_frame.to_dict("records"):
        peak = max(peak, float(row["high"]))
        trailing = _trail(entry_price, stop_price, peak, model, tp1_hit)
        if float(row["low"]) <= trailing:
            return {"hit": True, "stop_price": trailing, "hit_time": str(row.get("time")), "reason": model}
    return {"hit": False, "stop_price": trailing, "hit_time": None, "reason": model}


def _trail(entry: float, stop: float, peak: float, model: str, tp1_hit: bool) -> float:
    model = model.lower()
    if model == "break_even_after_tp1" and tp1_hit:
        return max(stop, entry)
    if model.startswith("peak_drawdown_"):
        pct = float(model.replace("peak_drawdown_", "").replace("_", ".").replace("p", "."))
        return max(stop, peak * (1 - pct / 100))
    if model == "m15_swing_low":
        return max(stop, peak * 0.985)
    if model == "m5_swing_low":
        return max(stop, peak * 0.992)
    if model == "zone_mid_break":
        return max(stop, entry * 1.002)
    return stop
