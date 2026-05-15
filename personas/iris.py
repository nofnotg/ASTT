from __future__ import annotations

from app.config import Settings, TradingMode, get_settings
from personas.base import PersonaResult


def analyze(context: dict, settings: Settings | None = None) -> PersonaResult:
    settings = settings or get_settings()
    market = context.get("market", "KRW-BTC")
    risk_reward = float(context.get("risk_reward", 0))
    spread_pct = float(context.get("spread_pct", 0))
    daily_loss_pct = float(context.get("daily_loss_pct", 0))
    open_positions = int(context.get("open_positions", 0))
    krw_amount = float(context.get("krw_amount", settings.min_order_krw))
    data_quality_warning = context.get("data_quality_warning")
    btc_shock = bool(context.get("btc_shock", False))
    veto_reason = None
    checks = [
        (risk_reward < 1.5, "risk_reward_below_1.5"),
        (bool(data_quality_warning), "data_quality_warning"),
        (btc_shock, "btc_shock"),
        (daily_loss_pct <= -abs(settings.max_daily_loss_pct), "max_daily_loss_reached"),
        (open_positions >= settings.max_open_positions, "max_open_positions_reached"),
        (krw_amount < settings.min_order_krw, "order_amount_below_minimum"),
        (spread_pct > 0.3, "spread_too_wide"),
        (settings.trading_mode == TradingMode.LIVE and not settings.live_trading_enabled, "live_guard_failed"),
    ]
    for failed, reason in checks:
        if failed:
            veto_reason = reason
            break
    veto = veto_reason is not None
    score = 35.0 if veto else 85.0
    decision = "VETO" if veto else "PASS"
    warnings = [data_quality_warning] if data_quality_warning else []
    return PersonaResult(
        persona_name="Iris",
        market=market,
        score=score,
        decision=decision,
        reasons=["risk guard completed" if not veto else f"veto: {veto_reason}"],
        warnings=warnings,
        veto=veto,
        veto_reason=veto_reason,
        payload={"risk_reward": risk_reward, "spread_pct": spread_pct, "daily_loss_pct": daily_loss_pct, "open_positions": open_positions},
    )
