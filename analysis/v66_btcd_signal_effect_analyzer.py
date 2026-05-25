from __future__ import annotations


def signal_decision(effect_krw: float) -> str:
    return "KEEP_AS_SOFT_WARNING" if float(effect_krw) < 0 else "DO_NOT_HARD_BLOCK"

