from __future__ import annotations

from typing import Any

from atr_precision_v2.atr_ltf_replayer import replay_trade_with_ltf
from atr_precision_v2.atr_path_schema import ATRReplayConfig


def reconstruct_trades(trades: list[dict[str, Any]], ltf_by_trade_id: dict[str, list[dict[str, Any]]], config: ATRReplayConfig) -> list[dict[str, Any]]:
    rows = []
    for trade in trades:
        trade_id = str(trade.get("trade_id"))
        rows.append(replay_trade_with_ltf(trade, ltf_by_trade_id.get(trade_id, []), config))
    return rows
