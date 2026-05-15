from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class SmallSeedConfig:
    capital_krw: float = 500000
    order_krw: float = 10000
    daily_reference_target_pct: float = 1.0
    weekly_reference_target_pct: float = 5.0
    monthly_reference_target_pct: float = 20.0


def calc_trade_pnl(
    capital_krw: float,
    order_krw: float,
    signal_pnl_pct: float,
    fee_pct: float = 0.05,
    slippage_pct: float = 0.15,
) -> dict:
    net_signal_pnl_pct = float(signal_pnl_pct) - (float(fee_pct) * 2) - float(slippage_pct)
    order_pnl_krw = float(order_krw) * net_signal_pnl_pct / 100
    account_pnl_pct = order_pnl_krw / float(capital_krw) * 100 if capital_krw else 0.0
    return {
        "capital_krw": float(capital_krw),
        "order_krw": float(order_krw),
        "gross_signal_pnl_pct": float(signal_pnl_pct),
        "fee_pct": float(fee_pct),
        "slippage_pct": float(slippage_pct),
        "net_signal_pnl_pct": net_signal_pnl_pct,
        "order_pnl_krw": order_pnl_krw,
        "account_pnl_pct": account_pnl_pct,
    }


def aggregate_small_seed_daily(rows: Iterable[dict], capital_krw: float = 500000) -> pd.DataFrame:
    frame = _as_frame(rows)
    if frame.empty:
        return _empty_daily()
    frame["date_kst"] = frame["date_kst"].astype(str)
    output = []
    equity = float(capital_krw)
    peak = equity
    consecutive_losses = 0
    for day, group in frame.groupby("date_kst", sort=True):
        entered = group[group.get("entered", True).astype(bool)] if "entered" in group else group
        entries = int(len(entered))
        pnl = float(entered["order_pnl_krw"].sum()) if entries and "order_pnl_krw" in entered else 0.0
        wins = int((entered["order_pnl_krw"].astype(float) > 0).sum()) if entries else 0
        losses = int((entered["order_pnl_krw"].astype(float) < 0).sum()) if entries else 0
        equity += pnl
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak * 100 if peak else 0.0
        if pnl < 0:
            consecutive_losses += 1
        elif entries:
            consecutive_losses = 0
        output.append(
            {
                "date_kst": day,
                "days": 1,
                "entry_days": 1 if entries else 0,
                "hold_days": 0 if entries else 1,
                "entries": entries,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / entries if entries else 0.0,
                "gross_signal_return_pct": float(entered["gross_signal_pnl_pct"].sum()) if entries and "gross_signal_pnl_pct" in entered else 0.0,
                "net_signal_return_pct": float(entered["net_signal_pnl_pct"].sum()) if entries and "net_signal_pnl_pct" in entered else 0.0,
                "order_pnl_krw": pnl,
                "account_return_pct": pnl / capital_krw * 100 if capital_krw else 0.0,
                "daily_account_pnl_pct": pnl / capital_krw * 100 if capital_krw else 0.0,
                "equity_krw": equity,
                "drawdown_pct": drawdown,
                "max_daily_loss_pct": min(0.0, pnl / capital_krw * 100 if capital_krw else 0.0),
                "consecutive_losses": consecutive_losses,
            }
        )
    return pd.DataFrame(output)


def aggregate_small_seed_weekly(daily_rows: Iterable[dict] | pd.DataFrame, capital_krw: float = 500000) -> pd.DataFrame:
    return _aggregate_period(daily_rows, "W-SUN", capital_krw, target_pct=5.0, target_key="weekly_target_gap_pct")


def aggregate_small_seed_monthly(daily_rows: Iterable[dict] | pd.DataFrame, capital_krw: float = 500000) -> pd.DataFrame:
    return _aggregate_period(daily_rows, "M", capital_krw, target_pct=20.0, target_key="monthly_target_gap_pct")


def summarize_trades(rows: Iterable[dict], capital_krw: float = 500000) -> dict:
    trades = _as_frame(rows)
    if trades.empty:
        return _summary_zero()
    daily = aggregate_small_seed_daily(trades, capital_krw)
    entries = int(len(trades))
    wins = int((trades["order_pnl_krw"].astype(float) > 0).sum()) if "order_pnl_krw" in trades else 0
    losses = int((trades["order_pnl_krw"].astype(float) < 0).sum()) if "order_pnl_krw" in trades else 0
    gross_profit = float(trades.loc[trades["order_pnl_krw"].astype(float) > 0, "order_pnl_krw"].sum())
    gross_loss = abs(float(trades.loc[trades["order_pnl_krw"].astype(float) < 0, "order_pnl_krw"].sum()))
    return {
        "entries": entries,
        "entry_count": entries,
        "entry_days": int(daily["entry_days"].sum()) if not daily.empty else 0,
        "hold_days": int(daily["hold_days"].sum()) if not daily.empty else 0,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / entries if entries else 0.0,
        "avg_signal_pnl_pct": float(trades["gross_signal_pnl_pct"].astype(float).mean()) if "gross_signal_pnl_pct" in trades else 0.0,
        "avg_net_signal_pnl_pct": float(trades["net_signal_pnl_pct"].astype(float).mean()) if "net_signal_pnl_pct" in trades else 0.0,
        "avg_order_pnl_krw": float(trades["order_pnl_krw"].astype(float).mean()) if "order_pnl_krw" in trades else 0.0,
        "total_order_pnl_krw": float(trades["order_pnl_krw"].astype(float).sum()) if "order_pnl_krw" in trades else 0.0,
        "account_return_pct": float(trades["order_pnl_krw"].astype(float).sum()) / capital_krw * 100 if capital_krw and "order_pnl_krw" in trades else 0.0,
        "max_drawdown_pct": float(daily["drawdown_pct"].min()) if not daily.empty else 0.0,
        "profit_factor": gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0),
        "avg_win_pct": float(trades.loc[trades["order_pnl_krw"].astype(float) > 0, "net_signal_pnl_pct"].mean()) if wins and "net_signal_pnl_pct" in trades else 0.0,
        "avg_loss_pct": float(trades.loc[trades["order_pnl_krw"].astype(float) < 0, "net_signal_pnl_pct"].mean()) if losses and "net_signal_pnl_pct" in trades else 0.0,
        "loss_day_count": int((daily["order_pnl_krw"].astype(float) < 0).sum()) if not daily.empty else 0,
        "consecutive_loss_max": int(daily["consecutive_losses"].max()) if not daily.empty else 0,
    }


def max_drawdown_from_pnl(pnl_values: Iterable[float], capital_krw: float) -> float:
    equity = float(capital_krw)
    peak = equity
    mdd = 0.0
    for value in pnl_values:
        equity += float(value)
        peak = max(peak, equity)
        drawdown = (equity - peak) / peak * 100 if peak else 0.0
        mdd = min(mdd, drawdown)
    return mdd


def _aggregate_period(daily_rows: Iterable[dict] | pd.DataFrame, freq: str, capital_krw: float, target_pct: float, target_key: str) -> pd.DataFrame:
    daily = _as_frame(daily_rows)
    if daily.empty:
        return pd.DataFrame()
    daily["period"] = pd.to_datetime(daily["date_kst"]).dt.to_period(freq).dt.start_time.dt.date.astype(str)
    output = []
    for period, group in daily.groupby("period", sort=True):
        entries = int(group["entries"].sum())
        wins = int(group["wins"].sum())
        pnl = float(group["order_pnl_krw"].sum())
        account_return = pnl / capital_krw * 100 if capital_krw else 0.0
        output.append(
            {
                "period": period,
                "days": int(len(group)),
                "entry_days": int(group["entry_days"].sum()),
                "hold_days": int(group["hold_days"].sum()),
                "entries": entries,
                "wins": wins,
                "losses": int(group["losses"].sum()),
                "win_rate": wins / entries if entries else 0.0,
                "gross_signal_return_pct": float(group["gross_signal_return_pct"].sum()),
                "net_signal_return_pct": float(group["net_signal_return_pct"].sum()),
                "order_pnl_krw": pnl,
                "account_return_pct": account_return,
                "max_daily_loss_pct": float(group["max_daily_loss_pct"].min()),
                "max_drawdown_pct": float(group["drawdown_pct"].min()),
                target_key: account_return - target_pct,
            }
        )
    return pd.DataFrame(output)


def _as_frame(rows: Iterable[dict] | pd.DataFrame) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows.copy()
    return pd.DataFrame(list(rows))


def _empty_daily() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date_kst",
            "days",
            "entry_days",
            "hold_days",
            "entries",
            "wins",
            "losses",
            "win_rate",
            "gross_signal_return_pct",
            "net_signal_return_pct",
            "order_pnl_krw",
            "account_return_pct",
            "daily_account_pnl_pct",
            "equity_krw",
            "drawdown_pct",
            "max_daily_loss_pct",
            "consecutive_losses",
        ]
    )


def _summary_zero() -> dict:
    return {
        "entries": 0,
        "entry_count": 0,
        "entry_days": 0,
        "hold_days": 0,
        "wins": 0,
        "losses": 0,
        "win_rate": 0.0,
        "avg_signal_pnl_pct": 0.0,
        "avg_net_signal_pnl_pct": 0.0,
        "avg_order_pnl_krw": 0.0,
        "total_order_pnl_krw": 0.0,
        "account_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "profit_factor": 0.0,
        "avg_win_pct": 0.0,
        "avg_loss_pct": 0.0,
        "loss_day_count": 0,
        "consecutive_loss_max": 0,
    }
