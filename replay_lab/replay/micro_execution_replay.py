from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from execution.micro_entry_engine import decide_micro_entry
from execution.micro_exit_engine import decide_micro_exit
from execution.response_state_machine import ResponseStateMachine
from features.micro_liquidity_features import compute_micro_liquidity_features
from features.micro_momentum_features import compute_micro_momentum_after_entry
from features.micro_signal_features import compute_micro_signal_features
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.edge_isolation_v54 import latest_edge_isolation_v54_experiment
from replay_lab.replay.second_candle_replay import replay_second_candles
from replay_lab.replay.structure_reversal_v5 import _load_base_frame


def run_micro_execution_replay(
    start_date,
    end_date,
    markets=None,
    top_markets: int = 30,
    fixed_order_krw: float = 10000,
    base_setup_source: str = "v5_simple",
    micro_entry_enabled: bool = True,
    micro_exit_enabled: bool = True,
    use_orderbook: bool = False,
    max_hold_seconds: int = 120,
    config: dict | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    start = pd.Timestamp(start_date).date()
    end = pd.Timestamp(end_date).date()
    exp_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_micro_execution")
    exp_dir = store_dir / "experiments" / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    setups, seed_meta = _load_setups(start, end, store_dir)
    trades = []
    data_quality_counts: dict[str, int] = {}
    for setup in setups.head(top_markets * 3).to_dict("records"):
        result = _run_one_setup(setup, fixed_order_krw, micro_entry_enabled, micro_exit_enabled, use_orderbook, max_hold_seconds, store_dir)
        if result:
            trades.append(result)
            data_quality_counts[result["data_quality"]] = data_quality_counts.get(result["data_quality"], 0) + 1
    trade_frame = pd.DataFrame(trades)
    if trade_frame.empty:
        trade_frame = pd.DataFrame(columns=["date_kst", "market", "entry_decision", "micro_exit_decision", "realized_pnl_pct", "order_pnl_krw", "hold_seconds", "data_quality"])
    metrics = _metrics(trade_frame, fixed_order_krw)
    metrics.update({"period": {"start_date": str(start), "end_date": str(end)}, "top_markets": top_markets, "fixed_order_krw": fixed_order_krw, "base_setup_source": base_setup_source, "micro_entry_enabled": micro_entry_enabled, "micro_exit_enabled": micro_exit_enabled, "use_orderbook": use_orderbook, "data_quality_summary": data_quality_counts, "seed_source": seed_meta, "live_readiness": _readiness(metrics, data_quality_counts)})
    trade_frame.to_parquet(exp_dir / "micro_trades.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (exp_dir / "config.json").write_text(json.dumps({"experiment_id": exp_id, "start_date": str(start), "end_date": str(end), "top_markets": top_markets, "fixed_order_krw": fixed_order_krw, "config": config or {}}, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def latest_micro_execution_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    exps = sorted((store_dir / "experiments").glob("exp_*_micro_execution"), key=lambda p: p.name)
    return exps[-1] if exps else None


def _load_setups(start: date, end: date, store_dir: Path) -> tuple[pd.DataFrame, dict]:
    exp = latest_edge_isolation_v54_experiment(store_dir)
    if exp and (exp / "edge_trades.parquet").exists():
        frame = pd.read_parquet(exp / "edge_trades.parquet")
        frame = frame[(frame["strategy_id"] == "MTF_ONLY") & (frame["exit_model"] == "FIXED_RR_1_5")].copy()
        frame = frame.sort_values(["date_kst", "market"]).groupby(["date_kst", "market"], as_index=False).head(1)
        mask = (pd.to_datetime(frame["date_kst"]).dt.date >= start) & (pd.to_datetime(frame["date_kst"]).dt.date <= end)
        cfg = json.loads((exp / "config.json").read_text(encoding="utf-8")) if (exp / "config.json").exists() else {}
        return frame[mask], {"experiment": exp.name, **cfg}
    return pd.DataFrame(), {"experiment": None, "empty_seed": True}


def _run_one_setup(setup: dict, fixed_order_krw: float, micro_entry_enabled: bool, micro_exit_enabled: bool, use_orderbook: bool, max_hold_seconds: int, store_dir: Path) -> dict | None:
    entry_time = pd.Timestamp(setup["entry_time_kst"])
    replay = replay_second_candles(setup["market"], entry_time - pd.Timedelta(seconds=10), entry_time + pd.Timedelta(seconds=max_hold_seconds), store_dir=store_dir)
    seconds = pd.DataFrame(replay["seconds"])
    if replay["data_quality"] == "UNAVAILABLE":
        seconds = _minute_proxy_seconds(setup, max_hold_seconds, store_dir)
        data_quality = "UNAVAILABLE"
    else:
        data_quality = replay["data_quality"]
    if seconds.empty:
        return None
    pre = seconds[pd.to_datetime(seconds["time"]) <= entry_time].copy()
    post = seconds[pd.to_datetime(seconds["time"]) > entry_time].copy()
    micro_signal = compute_micro_signal_features(pre)
    liquidity = compute_micro_liquidity_features([] if not use_orderbook else None)
    if not use_orderbook:
        liquidity.update({"best_ask_price": float(setup["entry_price"]), "best_bid_price": float(setup["entry_price"]) * 0.999, "spread_pct": 0.1, "liquidity_state": "GOOD", "warnings": ["orderbook_unavailable"]})
    machine = ResponseStateMachine()
    machine.on_setup({"market": setup["market"]})
    machine.arm_or_idle(True, "setup_and_risk_pass")
    entry_decision = decide_micro_entry({"setup_pass": True, "reference_price": setup["entry_price"]}, micro_signal, liquidity, {"btc_shock": False})
    if micro_entry_enabled and entry_decision["entry_decision"] == "CANCEL":
        machine.transition("IDLE", "micro_entry_cancel", context=entry_decision)
        return _cancel_row(setup, fixed_order_krw, data_quality, entry_decision, machine.history)
    entry_price = float(entry_decision["entry_price"] or setup["entry_price"])
    machine.enter({"entry_price": entry_price})
    machine.manage()
    entry_context = {"entry_price": entry_price, "target_price": float(setup.get("target_price", setup.get("target_1", entry_price * 1.006))), "stop_price": float(setup.get("stop_price", setup.get("zone_stop", entry_price * 0.994))), "max_hold_seconds": max_hold_seconds}
    post_micro = compute_micro_momentum_after_entry(post, entry_price, max_watch_seconds=min(30, max_hold_seconds))
    exit_decision = {"exit_decision": "TIME_STOP", "exit_price": float(post.iloc[-1]["close"]) if not post.empty else entry_price, "reason": ["no_post_seconds"], "warnings": []}
    for elapsed, row in enumerate(post.to_dict("records"), start=1):
        post_so_far = post.head(elapsed)
        post_micro = compute_micro_momentum_after_entry(post_so_far, entry_price)
        exit_decision = decide_micro_exit(entry_context, post_micro if micro_exit_enabled else {"micro_failure": False}, row, liquidity, elapsed)
        if exit_decision["exit_decision"] != "HOLD":
            break
    machine.exit(exit_decision["exit_decision"], exit_decision)
    machine.review()
    pnl_pct = (float(exit_decision["exit_price"]) - entry_price) / entry_price * 100 if entry_price else 0.0
    return {**setup, "entry_decision": entry_decision["entry_decision"], "micro_state": micro_signal["micro_state"], "buy_trade_ratio_5s": micro_signal["buy_trade_ratio_5s"], "price_change_5s_pct": micro_signal["price_change_5s_pct"], "micro_exit_decision": exit_decision["exit_decision"], "exit_price": exit_decision["exit_price"], "realized_pnl_pct": pnl_pct, "order_pnl_krw": fixed_order_krw * pnl_pct / 100, "hold_seconds": elapsed if "elapsed" in locals() else 0, "micro_failure": post_micro.get("micro_failure", False), "data_quality": data_quality, "orderbook_available": bool(use_orderbook), "state_history": machine.history}


def _minute_proxy_seconds(setup: dict, max_hold_seconds: int, store_dir: Path) -> pd.DataFrame:
    base = _load_base_frame(store_dir, setup["market"])
    entry_time = pd.Timestamp(setup["entry_time_kst"])
    window = base[(base["time"] >= entry_time) & (base["time"] <= entry_time + pd.Timedelta(minutes=3))].copy()
    if window.empty:
        return pd.DataFrame()
    rows = []
    for _, candle in window.iterrows():
        start = pd.Timestamp(candle["time"])
        for i in range(60):
            if len(rows) >= max_hold_seconds + 11:
                break
            frac = i / 59
            close = float(candle["open"]) + (float(candle["close"]) - float(candle["open"])) * frac
            rows.append({"time": start + pd.Timedelta(seconds=i), "open": close, "high": max(close, float(candle["high"])), "low": min(close, float(candle["low"])), "close": close, "volume": float(candle.get("volume", 0.0)) / 60, "synthetic": True})
    return pd.DataFrame(rows)


def _cancel_row(setup: dict, fixed_order_krw: float, data_quality: str, entry_decision: dict, history: list[dict]) -> dict:
    return {**setup, "entry_decision": "CANCEL", "micro_exit_decision": "NO_ENTRY", "exit_price": 0.0, "realized_pnl_pct": 0.0, "order_pnl_krw": 0.0, "hold_seconds": 0, "micro_failure": False, "data_quality": data_quality, "orderbook_available": False, "state_history": history, "veto_reasons": entry_decision.get("veto_reasons", [])}


def _metrics(trades: pd.DataFrame, fixed_order_krw: float) -> dict:
    if trades.empty:
        return {"entry_count": 0, "win_rate": 0.0, "profit_factor": 0.0, "expectancy_pct": 0.0, "avg_hold_seconds": 0.0, "micro_failure_exit_count": 0, "time_stop_count": 0, "take_profit_count": 0, "stop_loss_count": 0, "total_pnl_krw": 0.0}
    entered = trades[trades["entry_decision"] != "CANCEL"].copy()
    pnl = entered["realized_pnl_pct"].astype(float) if not entered.empty else pd.Series(dtype=float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float((wins / 100 * fixed_order_krw).sum())
    gross_loss = abs(float((losses / 100 * fixed_order_krw).sum()))
    return {"entry_count": int(len(entered)), "cancel_count": int((trades["entry_decision"] == "CANCEL").sum()), "win_rate": float((pnl > 0).mean()) if len(pnl) else 0.0, "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0), "expectancy_pct": float(pnl.mean()) if len(pnl) else 0.0, "avg_hold_seconds": float(entered["hold_seconds"].mean()) if not entered.empty else 0.0, "micro_failure_exit_count": int((entered["micro_exit_decision"] == "MICRO_FAILURE_EXIT").sum()) if not entered.empty else 0, "time_stop_count": int((entered["micro_exit_decision"] == "TIME_STOP").sum()) if not entered.empty else 0, "take_profit_count": int((entered["micro_exit_decision"] == "TAKE_PROFIT").sum()) if not entered.empty else 0, "stop_loss_count": int((entered["micro_exit_decision"] == "STOP_LOSS").sum()) if not entered.empty else 0, "total_pnl_krw": float(entered["order_pnl_krw"].sum()) if not entered.empty else 0.0}


def _readiness(metrics: dict, quality: dict) -> str:
    if quality.get("UNAVAILABLE", 0) > 0:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("entry_count", 0) < 30 or metrics.get("profit_factor", 0.0) < 1.1 or metrics.get("expectancy_pct", 0.0) <= 0:
        return "LIVE_NOT_ALLOWED"
    return "PAPER_MORE_REQUIRED"
