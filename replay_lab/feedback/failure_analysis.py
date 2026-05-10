from __future__ import annotations


def classify_failure(row: dict) -> str:
    if row.get("vetoed"):
        return "RISK_OVERRIDDEN"
    if row.get("exit_reason") == "stop_loss":
        return "WRONG_POSITION"
    if row.get("ambiguous_fill"):
        return "SLIPPAGE"
    return "TIMEOUT"

