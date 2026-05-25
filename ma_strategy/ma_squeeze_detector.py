from __future__ import annotations


def is_squeeze_breakout(states: list[str]) -> bool:
    return "MA_SQUEEZE_BREAKOUT" in states
