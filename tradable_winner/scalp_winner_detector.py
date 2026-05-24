from __future__ import annotations

from tradable_winner.tradable_winner_detector import _detect_one_window


def detect_scalp_winner(market: str, session_id: str, start_trade: dict, trades: list[dict], orderbooks: list[dict]) -> dict:
    return _detect_one_window(market, session_id, start_trade, trades, orderbooks, "TRADABLE_SCALP_WINNER")
