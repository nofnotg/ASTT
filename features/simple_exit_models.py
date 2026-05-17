from __future__ import annotations

import pandas as pd


EXIT_MODELS = ["FIXED_RR_1_0", "FIXED_RR_1_2", "FIXED_RR_1_5", "FIXED_RR_2_0", "ZONE_TARGET_FULL_EXIT", "TP1_BREAK_EVEN"]


def simulate_simple_exit(
    post_entry_frame,
    entry_price: float,
    stop_price: float,
    exit_model: str,
    target_space: dict | None = None,
    max_hold_minutes: int = 180,
) -> dict:
    frame = post_entry_frame.copy() if isinstance(post_entry_frame, pd.DataFrame) else pd.DataFrame(post_entry_frame or [])
    if frame.empty:
        return _row(exit_model, 0.0, "TIME_STOP", 0.0, 0.0, 0, False, False)
    frame = frame.head(max_hold_minutes)
    risk = max(entry_price - stop_price, entry_price * 0.003)
    target = _target(entry_price, risk, exit_model, target_space)
    break_even_armed = False
    mfe = (float(frame["high"].max()) - entry_price) / entry_price * 100
    mae = (float(frame["low"].min()) - entry_price) / entry_price * 100
    for idx, candle in enumerate(frame.to_dict("records"), start=1):
        low = float(candle["low"])
        high = float(candle["high"])
        if low <= stop_price:
            return _row(exit_model, (stop_price - entry_price) / entry_price * 100, "STOP_LOSS", mfe, mae, idx, False, True)
        if exit_model == "TP1_BREAK_EVEN" and high >= entry_price + risk:
            break_even_armed = True
        if break_even_armed and low <= entry_price:
            return _row(exit_model, 0.0, "BREAK_EVEN", mfe, mae, idx, True, False)
        if high >= target:
            return _row(exit_model, (target - entry_price) / entry_price * 100, "TAKE_PROFIT", mfe, mae, idx, True, False)
    last = float(frame.iloc[-1]["close"])
    return _row(exit_model, (last - entry_price) / entry_price * 100, "TIME_STOP", mfe, mae, int(len(frame)), False, False)


def _target(entry: float, risk: float, exit_model: str, target_space: dict | None) -> float:
    if exit_model == "ZONE_TARGET_FULL_EXIT" and target_space:
        return float(target_space.get("target_1", entry + risk))
    rr = {"FIXED_RR_1_0": 1.0, "FIXED_RR_1_2": 1.2, "FIXED_RR_1_5": 1.5, "FIXED_RR_2_0": 2.0, "TP1_BREAK_EVEN": 1.2}.get(exit_model, 1.0)
    return entry + risk * rr


def _row(exit_model: str, pnl: float, reason: str, mfe: float, mae: float, hold: int, hit_target: bool, hit_stop: bool) -> dict:
    return {
        "exit_model": exit_model,
        "realized_pnl_pct": float(pnl),
        "exit_reason": reason,
        "mfe_pct": float(mfe),
        "mae_pct": float(mae),
        "hold_minutes": int(hold),
        "hit_target": bool(hit_target),
        "hit_stop": bool(hit_stop),
    }
