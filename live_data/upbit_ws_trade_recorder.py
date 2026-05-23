from __future__ import annotations

from live_data.upbit_ws_message_normalizer import normalize_upbit_trade_message


def normalize_trade(raw: dict) -> dict:
    return normalize_upbit_trade_message(raw)
