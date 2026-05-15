from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import calc_trade_pnl, summarize_trades
from replay_lab.research.time_window_sweep_v3 import _load_market_frame


def run_preopen_confirmed_compare(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "small_seed_v3"
    out_dir.mkdir(parents=True, exist_ok=True)
    preopen = evaluate_entry_mode("preopen", start_date, end_date, markets, capital_krw, order_krw, store_dir)
    confirmed = evaluate_entry_mode("confirmed", start_date, end_date, markets, capital_krw, order_krw, store_dir)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "preopen": preopen["summary"],
        "confirmed": confirmed["summary"],
        "better_mode": choose_better_mode(preopen["summary"], confirmed["summary"]),
        "notes": [
            "PreOpen is faster, but false-breakout risk is higher.",
            "Confirmed is later, but can reduce weak 09:00 spikes.",
            "For a 500,000 KRW small seed, stability matters more than forcing entries.",
        ],
    }
    (out_dir / "preopen_confirmed_compare_v3.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not preopen["trades"].empty:
        preopen["trades"].to_parquet(out_dir / "preopen_trades_v3.parquet", index=False)
    if not confirmed["trades"].empty:
        confirmed["trades"].to_parquet(out_dir / "confirmed_trades_v3.parquet", index=False)
    return out_dir


def evaluate_entry_mode(
    mode: str,
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    store_dir: Path = REPLAY_STORE_DIR,
) -> dict:
    frames = {market: _load_market_frame(store_dir, market) for market in markets}
    rows = []
    day = start_date
    while day <= end_date:
        candidates = []
        for market, frame in frames.items():
            if frame.empty:
                continue
            candidate = _candidate_for_mode(frame, market, day, mode, capital_krw, order_krw)
            if candidate:
                candidates.append(candidate)
        if candidates:
            rows.append(max(candidates, key=lambda row: (row["candidate_score"], row["pre_trade_value_krw"], row["market"])))
        day += timedelta(days=1)
    trades = pd.DataFrame(rows)
    summary = _mode_summary(mode, trades, capital_krw)
    return {"summary": summary, "trades": trades}


def choose_better_mode(preopen: dict, confirmed: dict) -> str:
    pre_score = _mode_score(preopen)
    confirmed_score = _mode_score(confirmed)
    return "confirmed" if confirmed_score >= pre_score else "preopen"


def _candidate_for_mode(frame: pd.DataFrame, market: str, day: date, mode: str, capital_krw: float, order_krw: float) -> dict | None:
    scan_at = pd.Timestamp(datetime.combine(day, time(8, 50)))
    pre_decision_at = pd.Timestamp(datetime.combine(day, time(8, 59)))
    if mode == "confirmed":
        decision_at = pd.Timestamp(datetime.combine(day, time(9, 3)))
        entry_at = pd.Timestamp(datetime.combine(day, time(9, 4)))
    else:
        decision_at = pre_decision_at
        entry_at = pd.Timestamp(datetime.combine(day, time(9, 0)))
    force_exit = pd.Timestamp(datetime.combine(day, time(10, 0)))
    context = frame[(frame["candle_time_kst"] >= scan_at - pd.Timedelta(minutes=60)) & (frame["candle_time_kst"] < scan_at)]
    pre = frame[(frame["candle_time_kst"] >= scan_at) & (frame["candle_time_kst"] <= pre_decision_at)]
    observe = frame[(frame["candle_time_kst"] >= pd.Timestamp(datetime.combine(day, time(9, 0)))) & (frame["candle_time_kst"] <= decision_at)]
    outcome = frame[(frame["candle_time_kst"] >= entry_at) & (frame["candle_time_kst"] <= force_exit)]
    if pre.empty or outcome.empty:
        return None
    if mode == "confirmed" and observe.empty:
        return None
    context_avg = float(context["trade_price"].mean()) if not context.empty else float(pre["trade_price"].mean())
    pre_avg = float(pre["trade_price"].mean())
    pre_rvol = pre_avg / context_avg if context_avg else 0.0
    pre_return = _return_pct(pre)
    observe_return = _return_pct(observe) if not observe.empty else 0.0
    if mode == "confirmed" and observe_return < -0.2:
        return None
    candidate_score = min(pre_rvol, 4.0) * 20 + max(pre_return, 0.0) * 12 + max(observe_return, 0.0) * 16
    candles = outcome.rename(columns={"candle_time_kst": "time"})
    signal_price = float(candles.iloc[0]["open"])
    fill = simulate_long_trade(candles, signal_price, signal_price * 0.985, signal_price * 1.015, fee_pct=0.0, slippage_pct=0.0)
    pnl = calc_trade_pnl(capital_krw, order_krw, fill.pnl_pct, fee_pct=0.0, slippage_pct=0.0)
    return {
        "date_kst": day.isoformat(),
        "market": market,
        "mode": mode,
        "entered": bool(fill.entered),
        "candidate_score": candidate_score,
        "pre_rvol": pre_rvol,
        "pre_return_pct": pre_return,
        "observe_return_pct": observe_return,
        "pre_trade_value_krw": float(pre["trade_price"].sum()),
        "exit_reason": fill.exit_reason,
        "false_breakout_loss": bool(pre_return > 0 and pnl["order_pnl_krw"] < 0),
        "time_exit": fill.exit_reason == "timeout",
        **pnl,
    }


def _mode_summary(mode: str, trades: pd.DataFrame, capital_krw: float) -> dict:
    summary = summarize_trades(trades.to_dict("records"), capital_krw)
    if trades.empty:
        return {"mode": mode, **summary, "false_breakout_loss_count": 0, "missed_big_move_count": 0, "time_exit_count": 0}
    return {
        "mode": mode,
        **summary,
        "false_breakout_loss_count": int(trades.get("false_breakout_loss", pd.Series(dtype=bool)).astype(bool).sum()),
        "missed_big_move_count": int(((trades["pre_return_pct"].astype(float) > 0.8) & (trades["order_pnl_krw"].astype(float) <= 0)).sum()),
        "time_exit_count": int(trades.get("time_exit", pd.Series(dtype=bool)).astype(bool).sum()),
    }


def _mode_score(summary: dict) -> float:
    return summary.get("account_return_pct", 0.0) - abs(summary.get("max_drawdown_pct", 0.0)) * 0.7 + summary.get("profit_factor", 0.0) * 2


def _return_pct(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    start = float(frame.iloc[0]["open"])
    end = float(frame.iloc[-1]["close"])
    return (end - start) / start * 100 if start else 0.0
