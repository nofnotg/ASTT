from __future__ import annotations

from live_data.upbit_ws_message_normalizer import normalize_upbit_orderbook_message


def normalize_orderbook(raw: dict) -> dict:
    return normalize_upbit_orderbook_message(raw)
