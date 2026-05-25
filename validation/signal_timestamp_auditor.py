from __future__ import annotations

from typing import Any

from validation.lookahead_bias_checker import audit_trades_for_lookahead


def audit_signal_timestamps(trades: list[dict[str, Any]]) -> dict[str, Any]:
    return audit_trades_for_lookahead(trades)
