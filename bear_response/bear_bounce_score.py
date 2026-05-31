from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ELIGIBLE_MARKET_STATES = {
    "EDGE_DECAY",
    "RISK_OFF_ALT_WEAK",
    "BEAR_DEFENSE",
    "BEAR_BOUNCE_ONLY",
}

BLOCKED_MARKET_STATES = {"LOCKDOWN"}


@dataclass(frozen=True)
class BearBounceScore:
    score: int
    candidate: bool
    high_confidence: bool
    blocked: bool
    factors: list[str]
    missing_features: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "bear_bounce_score": self.score,
            "bear_bounce_candidate": self.candidate,
            "bear_bounce_high_confidence": self.high_confidence,
            "bear_bounce_blocked": self.blocked,
            "bear_bounce_factors": self.factors,
            "missing_bounce_features": self.missing_features,
        }


def score_bear_bounce(
    context: dict[str, Any],
    recent_journal: list[dict[str, Any]] | None = None,
    *,
    guard_on: bool = False,
    hard_guard: bool = False,
    drawdown_pct: float = 0.0,
) -> dict[str, Any]:
    """Score a paper-only bear bounce candidate using decision-time features only.

    The current historical ledger does not expose full intrabar RSI, depth, or
    spread. Those are recorded as missing features and replaced by conservative
    proxies available at signal time: setup tags, market state, BTC trend, BTC
    dominance deltas, recent realized edge, and high-watermark drawdown.
    """

    recent_journal = recent_journal or []
    trade = context.get("trade", {})
    state = context.get("state", {})
    feature = context.get("feature", {})
    btc = context.get("btc", {})
    market_state = str(state.get("market_state") or "")
    setup = str(trade.get("setup_type") or "")
    plan = str(trade.get("plan") or "")
    dominance_regime = str(state.get("dominance_regime") or "")
    btc_trend = str(state.get("btc_trend") or btc.get("btc_price_trend_1d") or "")

    score = 0
    factors: list[str] = []
    missing = ["rsi_intrabar", "spread_depth", "volume_climax", "candlestick_tail"]
    blocked = market_state in BLOCKED_MARKET_STATES

    if market_state in ELIGIBLE_MARKET_STATES:
        score += 15
        factors.append("BEAR_CONTEXT_MARKET_STATE")
    elif guard_on or drawdown_pct <= -10.0:
        score += 10
        factors.append("BEAR_CONTEXT_LOSS_GUARD_PROXY")

    if "LIQUIDITY_SWEEP" in setup:
        score += 15
        factors.append("LIQUIDITY_SWEEP_RECLAIM_PROXY")
    if "FVG_OB_OVERLAP" in setup or "FVG" in setup or "OB" in setup:
        score += 10
        factors.append("FVG_OB_REACTION")
    if plan == "PLAN_A_ICT_FAT_TAIL":
        score += 10
        factors.append("PLAN_A_STRONG_SETUP")

    recent_rows = [row for row in recent_journal[-20:] if row.get("defense_action") == "ENTER"]
    recent_losses = sum(1 for row in recent_rows if float(row.get("pnl_krw", 0.0)) < 0.0)
    recent_pf = _profit_factor(recent_rows)
    if len(recent_rows) >= 10 and (recent_losses >= 5 or recent_pf < 1.0):
        score += 15
        factors.append("RECENT_SELLING_PRESSURE_PROXY")
    if hard_guard:
        score += 10
        factors.append("HARD_GUARD_OVERSOLD_PROXY")

    delta_1h = _float(feature.get("btcdom_delta_1h"))
    delta_4h = _float(feature.get("btcdom_delta_4h"))
    delta_24h = _float(feature.get("btcdom_delta_24h"))
    if delta_1h is not None and delta_1h <= 0:
        score += 5
        factors.append("DOMINANCE_EASING_1H")
    if delta_4h is not None and delta_24h is not None and delta_4h < delta_24h:
        score += 5
        factors.append("DOMINANCE_RISE_SLOWING")
    if dominance_regime in {"BTCDOM_STABLE", "BTCDOM_DOWN", "BTCDOM_EASING"}:
        score += 5
        factors.append("DOMINANCE_NOT_ACCELERATING")

    if btc_trend in {"UP", "SIDEWAYS", "RANGE"}:
        score += 10
        factors.append("BTC_NOT_BREAKING_DOWN")
    if str(btc.get("btc_structure") or "") == "RANGE":
        score += 5
        factors.append("BTC_RANGE_RECLAIM_PROXY")

    if drawdown_pct <= -15.0:
        score += 5
        factors.append("DEEP_HWM_DRAWDOWN_CONTEXT")

    score = max(0, min(100, score))
    candidate = score >= 60 and not blocked
    high_confidence = score >= 75 and not blocked
    return BearBounceScore(score, candidate, high_confidence, blocked, factors, missing).as_dict()


def _profit_factor(rows: list[dict[str, Any]]) -> float:
    wins = sum(float(row.get("pnl_krw", 0.0)) for row in rows if float(row.get("pnl_krw", 0.0)) > 0.0)
    losses = abs(sum(float(row.get("pnl_krw", 0.0)) for row in rows if float(row.get("pnl_krw", 0.0)) < 0.0))
    if losses:
        return wins / losses
    if wins:
        return 99.0
    return 0.0


def _float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
