from __future__ import annotations

import pandas as pd

from execution.micro_entry_engine import decide_micro_entry
from execution.micro_exit_engine import decide_micro_exit
from features.micro_cost_model import apply_micro_cost_model
from features.micro_liquidity_features import compute_micro_liquidity_features
from features.micro_momentum_features import compute_micro_momentum_after_entry
from features.micro_signal_features import compute_micro_signal_features


def replay_candidate_second_window(candidate_event: dict, second_window: dict, fixed_order_krw: float = 10000, micro_entry_enabled: bool = True, micro_exit_enabled: bool = True, cost_scenario: str = "realistic_1") -> dict:
    candidate_time = pd.Timestamp(candidate_event.get("candidate_time") or second_window["candidate_time"])
    seconds = pd.DataFrame(second_window.get("seconds", []))
    if seconds.empty or second_window.get("data_quality") == "UNAVAILABLE":
        return _observation(candidate_event, second_window, "CANCEL", ["second_window_unavailable"])
    seconds["time"] = pd.to_datetime(seconds["time"])
    pre = seconds[seconds["time"] <= candidate_time].copy()
    post = seconds[seconds["time"] > candidate_time].copy()
    signal = compute_micro_signal_features(pre, as_of_time=candidate_time)
    liquidity = compute_micro_liquidity_features([{"best_ask_price": candidate_event.get("reference_price", float(pre.iloc[-1]["close"])), "best_bid_price": candidate_event.get("reference_price", float(pre.iloc[-1]["close"])) * 0.999, "best_ask_size": 10, "best_bid_size": 10}])
    entry = decide_micro_entry({"setup_pass": True, "reference_price": candidate_event.get("reference_price", float(pre.iloc[-1]["close"]))}, signal, liquidity, {"btc_shock": False})
    if micro_entry_enabled and entry["entry_decision"] in {"CANCEL", "WAIT"}:
        reason = entry.get("veto_reasons") or entry.get("reason") or [f"micro_entry_{entry['entry_decision'].lower()}"]
        return _observation(candidate_event, second_window, entry["entry_decision"], reason)
    entry_price = float(entry.get("entry_price") or candidate_event.get("reference_price") or pre.iloc[-1]["close"])
    target = float(candidate_event.get("target_price", entry_price * 1.006))
    stop = float(candidate_event.get("stop_price", entry_price * 0.994))
    exit_result = {"exit_decision": "TIME_STOP", "exit_price": float(post.iloc[-1]["close"]) if not post.empty else entry_price, "reason": ["end_of_window"]}
    elapsed = 0
    post_micro = {}
    for elapsed, row in enumerate(post.to_dict("records"), start=1):
        post_so_far = post.head(elapsed)
        post_micro = compute_micro_momentum_after_entry(post_so_far, entry_price)
        exit_result = decide_micro_exit({"entry_price": entry_price, "target_price": target, "stop_price": stop, "max_hold_seconds": 120}, post_micro if micro_exit_enabled else {"micro_failure": False}, row, liquidity, elapsed)
        if exit_result["exit_decision"] != "HOLD":
            break
    gross = (float(exit_result["exit_price"]) - entry_price) / entry_price * 100 if entry_price else 0.0
    costed = apply_micro_cost_model({"realized_pnl_pct": gross}, cost_scenario)
    return {"candidate_id": second_window.get("candidate_id"), "market": second_window["market"], "candidate_time": second_window["candidate_time"], "data_source": "UPBIT_REST_SECONDS", "data_quality": second_window.get("data_quality"), "entry_decision": "ENTER", "position_created": True, "included_in_pnl": True, "observation_only": False, "entry_time": candidate_time.isoformat(), "entry_price": entry_price, "exit_time": (candidate_time + pd.Timedelta(seconds=elapsed)).isoformat(), "exit_price": float(exit_result["exit_price"]), "exit_reason": exit_result["exit_decision"], "gross_pnl_pct": gross, "net_pnl_pct": costed["net_pnl_pct"], "net_pnl_krw": fixed_order_krw * costed["net_pnl_pct"] / 100, "mfe_pct": post_micro.get("mfe_10s_pct", 0.0), "mae_pct": post_micro.get("mae_10s_pct", 0.0), "hold_seconds": elapsed, "reason": entry.get("reason", []), "warnings": []}


def _observation(candidate_event: dict, second_window: dict, decision: str, reasons: list[str]) -> dict:
    return {
        "candidate_id": second_window.get("candidate_id") or candidate_event.get("candidate_id"),
        "market": second_window.get("market") or candidate_event.get("market"),
        "candidate_time": second_window.get("candidate_time") or candidate_event.get("candidate_time"),
        "data_source": second_window.get("data_source", "UPBIT_REST_SECONDS"),
        "data_quality": second_window.get("data_quality", "UNAVAILABLE"),
        "entry_decision": decision,
        "position_created": False,
        "included_in_pnl": False,
        "observation_only": True,
        "entry_time": None,
        "entry_price": None,
        "exit_time": None,
        "exit_price": None,
        "exit_reason": None,
        "gross_pnl_pct": None,
        "net_pnl_pct": None,
        "net_pnl_krw": None,
        "mfe_pct": None,
        "mae_pct": None,
        "hold_seconds": 0,
        "reason": reasons,
        "warnings": reasons,
    }
