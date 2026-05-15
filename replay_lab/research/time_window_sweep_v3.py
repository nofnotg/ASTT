from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd

from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import calc_trade_pnl, summarize_trades


DEFAULT_WINDOWS = ["00:00", "01:00", "05:00", "09:00", "10:00", "13:00", "17:00", "21:00", "22:30", "23:00"]


def default_windows(step_minutes: int | None = None) -> list[str]:
    if not step_minutes:
        return DEFAULT_WINDOWS
    values = []
    current = datetime.combine(date(2026, 1, 1), time.min)
    end = datetime.combine(date(2026, 1, 1), time.max)
    while current <= end:
        if current + timedelta(minutes=60) <= end:
            values.append(current.strftime("%H:%M"))
        current += timedelta(minutes=step_minutes)
    return values


def run_time_window_sweep_v3(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    step_minutes: int | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    out_dir = store_dir / "reports" / "small_seed_v3"
    out_dir.mkdir(parents=True, exist_ok=True)
    windows = default_windows(step_minutes)
    rows, trades = evaluate_time_windows(start_date, end_date, markets, windows, capital_krw, order_krw, store_dir)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "rows": rows,
    }
    (out_dir / "time_window_sweep_v3.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_parquet(out_dir / "time_window_sweep_v3.parquet", index=False)
    if not trades.empty:
        trades.to_parquet(out_dir / "time_window_sweep_trades_v3.parquet", index=False)
    return out_dir


def evaluate_time_windows(
    start_date: date,
    end_date: date,
    markets: list[str],
    windows: Iterable[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    store_dir: Path = REPLAY_STORE_DIR,
) -> tuple[list[dict], pd.DataFrame]:
    frames = {market: _load_market_frame(store_dir, market) for market in markets}
    trade_rows = []
    day = start_date
    while day <= end_date:
        for window in windows:
            candidates = []
            for market, frame in frames.items():
                if frame.empty:
                    continue
                candidate = _evaluate_candidate_window(frame, market, day, window, capital_krw, order_krw)
                if candidate:
                    candidates.append(candidate)
            if candidates:
                best = max(candidates, key=lambda row: (row["candidate_score"], row["pre_trade_value_krw"], row["market"]))
                trade_rows.append(best)
        day += timedelta(days=1)
    trades = pd.DataFrame(trade_rows)
    rows = []
    if trades.empty:
        return rows, trades
    for window, group in trades.groupby("window", sort=True):
        summary = summarize_trades(group.to_dict("records"), capital_krw)
        risk_score = _risk_adjusted_score(summary)
        rows.append(
            {
                "window": window,
                "sessions": int(group["date_kst"].nunique()),
                "candidate_count": int(len(group)),
                "entry_count": summary["entry_count"],
                "win_rate": summary["win_rate"],
                "avg_net_signal_pnl_pct": summary["avg_net_signal_pnl_pct"],
                "total_order_pnl_krw": summary["total_order_pnl_krw"],
                "account_return_pct": summary["account_return_pct"],
                "max_drawdown_pct": summary["max_drawdown_pct"],
                "profit_factor": summary["profit_factor"],
                "risk_adjusted_score": risk_score,
            }
        )
    return sorted(rows, key=lambda row: row["risk_adjusted_score"], reverse=True), trades


def _evaluate_candidate_window(frame: pd.DataFrame, market: str, day: date, window: str, capital_krw: float, order_krw: float) -> dict | None:
    entry_at = pd.Timestamp(datetime.combine(day, _parse_time(window)))
    if entry_at.time() < time(0, 10) or entry_at + pd.Timedelta(minutes=60) > pd.Timestamp(datetime.combine(day, time.max)):
        return None
    scan_start = entry_at - pd.Timedelta(minutes=10)
    context_start = entry_at - pd.Timedelta(minutes=70)
    force_exit = entry_at + pd.Timedelta(minutes=60)
    context = frame[(frame["candle_time_kst"] >= context_start) & (frame["candle_time_kst"] < scan_start)]
    pre = frame[(frame["candle_time_kst"] >= scan_start) & (frame["candle_time_kst"] < entry_at)]
    outcome = frame[(frame["candle_time_kst"] >= entry_at) & (frame["candle_time_kst"] <= force_exit)]
    if pre.empty or outcome.empty:
        return None
    context_avg = float(context["trade_price"].mean()) if not context.empty else float(pre["trade_price"].mean())
    pre_avg = float(pre["trade_price"].mean())
    pre_rvol = pre_avg / context_avg if context_avg else 0.0
    pre_return = (float(pre.iloc[-1]["close"]) - float(pre.iloc[0]["open"])) / float(pre.iloc[0]["open"]) * 100 if float(pre.iloc[0]["open"]) else 0.0
    candidate_score = max(0.0, min(pre_rvol, 4.0) * 20 + max(pre_return, 0.0) * 12)
    candles = outcome.rename(columns={"candle_time_kst": "time"})
    signal_price = float(candles.iloc[0]["open"])
    fill = simulate_long_trade(candles, signal_price, signal_price * 0.985, signal_price * 1.015, fee_pct=0.0, slippage_pct=0.0)
    pnl = calc_trade_pnl(capital_krw, order_krw, fill.pnl_pct, fee_pct=0.0, slippage_pct=0.0)
    return {
        "date_kst": day.isoformat(),
        "market": market,
        "window": window,
        "entered": bool(fill.entered),
        "candidate_score": candidate_score,
        "pre_rvol": pre_rvol,
        "pre_return_pct": pre_return,
        "pre_trade_value_krw": float(pre["trade_price"].sum()),
        "exit_reason": fill.exit_reason,
        **pnl,
    }


def _risk_adjusted_score(summary: dict) -> float:
    return round(
        summary["account_return_pct"]
        - abs(summary["max_drawdown_pct"]) * 0.7
        + summary["profit_factor"] * 2
        + min(summary["entry_count"] / 50, 1) * 5,
        4,
    )


def _load_market_frame(store_dir: Path, market: str) -> pd.DataFrame:
    path = store_dir / "normalized" / "candles_1m" / f"{market}.parquet"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame["candle_time_kst"] = pd.to_datetime(frame["candle_time_kst"])
    return frame.sort_values("candle_time_kst")


def _parse_time(value: str) -> time:
    hour, minute = [int(part) for part in value.split(":")]
    return time(hour, minute)
