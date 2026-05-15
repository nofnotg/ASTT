from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class FillReplayResult:
    entered: bool
    entry_price: float
    exit_price: float
    exit_reason: str
    pnl_pct: float
    fee_pct: float
    slippage_pct: float
    ambiguous_fill: bool = False


def simulate_long_trade(
    candles: pd.DataFrame,
    signal_price: float,
    stop_loss: float,
    take_profit: float,
    fee_pct: float = 0.05,
    slippage_pct: float = 0.15,
    ambiguous_fill_policy: str = "stop_first",
) -> FillReplayResult:
    if candles is None or candles.empty:
        return FillReplayResult(False, 0, 0, "no_outcome_data", 0, fee_pct, slippage_pct)
    entry = float(candles.iloc[0]["open"]) if "open" in candles else signal_price
    entry *= 1 + slippage_pct / 100
    exit_price = float(candles.iloc[-1]["close"])
    exit_reason = "timeout"
    ambiguous = False
    for _, row in candles.iterrows():
        hit_stop = float(row["low"]) <= stop_loss
        hit_target = float(row["high"]) >= take_profit
        if hit_stop and hit_target:
            ambiguous = True
            if ambiguous_fill_policy == "stop_first":
                exit_price = stop_loss * (1 - slippage_pct / 100)
                exit_reason = "stop_loss"
            else:
                exit_price = take_profit * (1 - slippage_pct / 100)
                exit_reason = "take_profit"
            break
        if hit_stop:
            exit_price = stop_loss * (1 - slippage_pct / 100)
            exit_reason = "stop_loss"
            break
        if hit_target:
            exit_price = take_profit * (1 - slippage_pct / 100)
            exit_reason = "take_profit"
            break
    gross_pct = (exit_price - entry) / entry * 100 if entry else 0.0
    net_pct = gross_pct - (fee_pct * 2)
    return FillReplayResult(True, entry, exit_price, exit_reason, net_pct, fee_pct, slippage_pct, ambiguous)

