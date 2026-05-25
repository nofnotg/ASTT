from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class RollingEdgeStats:
    trade_count: int = 0
    win_rate_pct: float = 100.0
    profit_factor: float = 99.0


class DynamicRiskScaler:
    def __init__(self, windows: tuple[int, ...] = (20, 30)) -> None:
        self.max_window = max(windows)
        self._pnls: deque[float] = deque(maxlen=self.max_window)
        self._last_result_time: str | None = None

    def record(self, pnl_krw: float, result_time: str | None = None) -> None:
        self._pnls.append(float(pnl_krw))
        self._last_result_time = result_time or self._last_result_time

    def stats(self, window: int = 20) -> RollingEdgeStats:
        values = list(self._pnls)[-window:]
        if not values:
            return RollingEdgeStats()
        wins = [value for value in values if value > 0]
        losses = [value for value in values if value < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        return RollingEdgeStats(
            trade_count=len(values),
            win_rate_pct=len(wins) / len(values) * 100,
            profit_factor=gross_win / gross_loss if gross_loss else 99.0,
        )

    def audit_window(self, window: int = 20) -> dict[str, Any]:
        stats = self.stats(window)
        return {
            "rolling_window_end_time": self._last_result_time,
            "rolling_trades_used": stats.trade_count,
            "rolling_win_rate_pct": stats.win_rate_pct,
            "rolling_profit_factor": stats.profit_factor,
        }
