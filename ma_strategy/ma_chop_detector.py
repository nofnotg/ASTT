from __future__ import annotations


def is_ma_chop(states: list[str]) -> bool:
    return "MA_CHOP" in states or "TESTA_CHOP" in states
