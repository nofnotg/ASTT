from __future__ import annotations


HARD_NO_TRADE_STATES = {"MA_BEAR", "TESTA_LOST_75"}


def should_no_trade(states: list[str]) -> bool:
    return any(state in HARD_NO_TRADE_STATES for state in states)
