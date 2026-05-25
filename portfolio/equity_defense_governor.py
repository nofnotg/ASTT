from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DefensePolicy:
    name: str
    rolling_edge_throttle: bool = False
    drawdown_throttle: bool = False
    drawdown_stop: bool = False
    loss_streak_pause: bool = False
    market_cooldown: bool = False
    riskoff_hard_stop: bool = False
    rolling_window: int = 20
    rolling_min_win_rate_pct: float = 35.0
    rolling_min_profit_factor: float = 0.8
    rolling_multiplier: float = 0.35
    drawdown_threshold_pct: float = -10.0
    drawdown_multiplier: float = 0.5
    stop_drawdown_pct: float = -20.0
    pause_loss_streak: int = 10
    market_cooldown_days: int = 30


POLICIES: dict[str, DefensePolicy] = {
    "BASELINE": DefensePolicy("BASELINE"),
    "DRAWDOWN_THROTTLE": DefensePolicy("DRAWDOWN_THROTTLE", drawdown_throttle=True),
    "ROLLING_EDGE_THROTTLE": DefensePolicy("ROLLING_EDGE_THROTTLE", rolling_edge_throttle=True),
    "HYBRID_DEFENSE": DefensePolicy("HYBRID_DEFENSE", rolling_edge_throttle=True, drawdown_throttle=True),
    "HARD_NO_TRADE_REFERENCE": DefensePolicy(
        "HARD_NO_TRADE_REFERENCE",
        rolling_edge_throttle=True,
        drawdown_throttle=True,
        drawdown_stop=True,
        loss_streak_pause=True,
        market_cooldown=True,
        riskoff_hard_stop=True,
    ),
}


class EquityDefenseGovernor:
    def __init__(self, policy: DefensePolicy, initial_cash_krw: float = 500000) -> None:
        self.policy = policy
        self.equity = float(initial_cash_krw)
        self.peak = float(initial_cash_krw)
        self.recent_pnls: deque[float] = deque(maxlen=policy.rolling_window)
        self.loss_streak = 0
        self.market_loss_counts: dict[str, int] = {}
        self.market_cooldown_until: dict[str, str] = {}

    def evaluate(self, trade: dict[str, Any], previous_month_market: dict[str, Any] | None = None) -> dict[str, Any]:
        multiplier = 1.0
        reasons: list[str] = []
        action = "ENTER"
        current_drawdown_pct = self._current_drawdown_pct()

        if self.policy.rolling_edge_throttle and len(self.recent_pnls) >= self.policy.rolling_window:
            rolling = self._rolling_stats()
            if rolling["win_rate_pct"] < self.policy.rolling_min_win_rate_pct or rolling["profit_factor"] < self.policy.rolling_min_profit_factor:
                multiplier = min(multiplier, self.policy.rolling_multiplier)
                reasons.append("ROLLING_EDGE_THROTTLE")

        if self.policy.drawdown_throttle and current_drawdown_pct <= self.policy.drawdown_threshold_pct:
            multiplier = min(multiplier, self.policy.drawdown_multiplier)
            reasons.append("DRAWDOWN_THROTTLE_10")

        if self.policy.drawdown_stop and current_drawdown_pct <= self.policy.stop_drawdown_pct:
            action = "SKIP"
            reasons.append("DRAWDOWN_STOP_20")

        if self.policy.loss_streak_pause and self.loss_streak >= self.policy.pause_loss_streak:
            action = "SKIP"
            reasons.append("LOSS_STREAK_PAUSE")

        market = str(trade.get("market", ""))
        if self.policy.market_cooldown and market in self.market_cooldown_until:
            if str(trade.get("entry_time", ""))[:10] <= self.market_cooldown_until[market]:
                action = "SKIP"
                reasons.append("MARKET_COOLDOWN")

        if self.policy.riskoff_hard_stop and previous_month_market:
            if float(previous_month_market.get("positive_market_pct", 100.0)) < 25.0:
                action = "SKIP"
                reasons.append("PREV_MONTH_BREADTH_LOW")
            if float(previous_month_market.get("avg_return_pct", 0.0)) < -10.0:
                action = "SKIP"
                reasons.append("PREV_MONTH_AVG_RETURN_WEAK")

        return {
            "defense_mode": self.policy.name,
            "risk_multiplier_before_defense": 1.0,
            "risk_multiplier_after_defense": 0.0 if action == "SKIP" else multiplier,
            "defense_reasons": reasons,
            "defense_action": action,
            "rolling_stats_before": self._rolling_stats(),
            "drawdown_before_pct": current_drawdown_pct,
            "would_have_entered_baseline": True,
        }

    def record_result(self, trade: dict[str, Any], simulated_pnl_krw: float) -> None:
        self.equity += simulated_pnl_krw
        self.peak = max(self.peak, self.equity)
        self.recent_pnls.append(simulated_pnl_krw)
        if simulated_pnl_krw < 0:
            self.loss_streak += 1
            market = str(trade.get("market", ""))
            self.market_loss_counts[market] = self.market_loss_counts.get(market, 0) + 1
            if self.policy.market_cooldown and self.market_loss_counts[market] >= 3:
                self.market_cooldown_until[market] = _add_days(str(trade.get("entry_time", ""))[:10], self.policy.market_cooldown_days)
                self.market_loss_counts[market] = 0
        else:
            self.loss_streak = 0

    def _current_drawdown_pct(self) -> float:
        return (self.equity - self.peak) / self.peak * 100 if self.peak else 0.0

    def _rolling_stats(self) -> dict[str, float]:
        if not self.recent_pnls:
            return {"trade_count": 0, "win_rate_pct": 100.0, "profit_factor": 99.0}
        wins = [pnl for pnl in self.recent_pnls if pnl > 0]
        losses = [pnl for pnl in self.recent_pnls if pnl < 0]
        gross_win = sum(wins)
        gross_loss = abs(sum(losses))
        return {
            "trade_count": len(self.recent_pnls),
            "win_rate_pct": len(wins) / len(self.recent_pnls) * 100,
            "profit_factor": gross_win / gross_loss if gross_loss else 99.0,
        }


def _add_days(date_text: str, days: int) -> str:
    from datetime import datetime, timedelta

    try:
        return (datetime.fromisoformat(date_text) + timedelta(days=days)).date().isoformat()
    except ValueError:
        return date_text
