from __future__ import annotations

import pandas as pd


RUNNER_MODELS = {
    "NO_RUNNER": {"tp1": 0.5, "tp2": 0.5, "runner": 0.0},
    "SMALL_RUNNER": {"tp1": 0.5, "tp2": 0.4, "runner": 0.1},
    "BALANCED_RUNNER": {"tp1": 0.4, "tp2": 0.4, "runner": 0.2},
    "AGGRESSIVE_RUNNER": {"tp1": 0.3, "tp2": 0.4, "runner": 0.3},
}


def simulate_runner_exit(
    post_entry_frame: pd.DataFrame,
    entry_price: float,
    stop_price: float,
    exit_plan: dict,
    target_space: dict,
    trailing_model: str,
) -> dict:
    if post_entry_frame is None or post_entry_frame.empty:
        return _result(0.0, False, False, "NO_DATA", 0.0, 0.0, 0.0, 0.0)
    data = post_entry_frame.copy()
    tp1 = float(target_space.get("target_1", entry_price * 1.01))
    tp2 = float(target_space.get("target_2", max(tp1, entry_price * 1.02)))
    target3 = float(target_space.get("target_3", max(tp2, entry_price * 1.03)))
    splits = _splits(exit_plan)
    realized = 0.0
    open_runner = splits["runner"]
    tp1_hit = False
    tp2_hit = False
    peak = entry_price
    runner_exit_reason = "TIME_STOP"
    runner_contrib = 0.0

    for row in data.to_dict("records"):
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        peak = max(peak, high)
        if low <= stop_price and not tp1_hit:
            realized += -abs((entry_price - stop_price) / entry_price * 100)
            return _result(realized, False, False, "STOP", 0.0, _mfe(data, entry_price), _mae(data, entry_price), 0.0)
        if high >= tp1 and not tp1_hit:
            tp1_hit = True
            realized += splits["tp1"] * ((tp1 - entry_price) / entry_price * 100)
        if high >= tp2 and tp1_hit and not tp2_hit:
            tp2_hit = True
            realized += splits["tp2"] * ((tp2 - entry_price) / entry_price * 100)
        if open_runner > 0 and tp1_hit:
            if high >= target3:
                runner_contrib = open_runner * ((target3 - entry_price) / entry_price * 100)
                runner_exit_reason = "TARGET_3"
                realized += runner_contrib
                open_runner = 0
                break
            trailing_stop = _trailing_stop(entry_price, stop_price, peak, trailing_model, tp1_hit)
            if low <= trailing_stop:
                runner_contrib = open_runner * ((trailing_stop - entry_price) / entry_price * 100)
                runner_exit_reason = "TRAILING_STOP"
                realized += runner_contrib
                open_runner = 0
                break
        if close <= stop_price and tp1_hit and open_runner > 0:
            runner_contrib = open_runner * ((stop_price - entry_price) / entry_price * 100)
            runner_exit_reason = "STOP"
            realized += runner_contrib
            open_runner = 0
            break

    if open_runner > 0:
        last_close = float(data.iloc[-1]["close"])
        runner_contrib = open_runner * ((last_close - entry_price) / entry_price * 100)
        realized += runner_contrib
    mfe = _mfe(data, entry_price)
    mae = _mae(data, entry_price)
    return _result(realized, tp1_hit, tp2_hit, runner_exit_reason, runner_contrib, mfe, mae, realized / max(mfe, 0.01))


def _splits(exit_plan: dict) -> dict:
    model = str(exit_plan.get("runner_model", "")).upper()
    if model in RUNNER_MODELS:
        return RUNNER_MODELS[model]
    runner = float(exit_plan.get("runner_ratio", 0.0))
    return {"tp1": max(0.0, 0.6 - runner / 2), "tp2": max(0.0, 0.4 - runner / 2), "runner": runner}


def _trailing_stop(entry: float, stop: float, peak: float, model: str, tp1_hit: bool) -> float:
    model = model.lower()
    if model == "break_even_after_tp1" and tp1_hit:
        return max(stop, entry)
    if model.startswith("peak_drawdown_"):
        pct = float(model.replace("peak_drawdown_", "").replace("_", ".").replace("p", "."))
        return max(stop, peak * (1 - pct / 100))
    if model in {"m15_swing_low", "m5_swing_low", "zone_mid_break"}:
        return max(stop, peak * 0.985)
    return max(stop, peak * 0.98)


def _mfe(frame: pd.DataFrame, entry: float) -> float:
    return (float(frame["high"].max()) - entry) / entry * 100


def _mae(frame: pd.DataFrame, entry: float) -> float:
    return (float(frame["low"].min()) - entry) / entry * 100


def _result(realized, tp1, tp2, reason, runner_contrib, mfe, mae, capture) -> dict:
    return {
        "realized_pnl_pct": float(realized),
        "tp1_hit": bool(tp1),
        "tp2_hit": bool(tp2),
        "runner_exit_reason": reason,
        "runner_contribution_pct": float(runner_contrib),
        "runner_contribution_krw": 0.0,
        "max_favorable_excursion_pct": float(mfe),
        "max_adverse_excursion_pct": float(mae),
        "capture_ratio": float(capture),
    }
