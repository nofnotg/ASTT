from __future__ import annotations


def is_overextended(states: list[str]) -> bool:
    return "MA_OVEREXTENDED" in states
