from __future__ import annotations

from app.config import Settings, get_settings
from personas.base import PersonaResult, decision_from_score


def analyze(context: dict, settings: Settings | None = None) -> PersonaResult:
    settings = settings or get_settings()
    market = context.get("market", "KRW-BTC")
    price = float(context.get("price") or 0)
    steps = [settings.costa_step_1_krw, settings.costa_step_2_krw, settings.costa_step_3_krw]
    total = sum(steps)
    avg_price = price if price else 0
    escape_price = avg_price * (1 + settings.costa_take_profit_pct / 100) if avg_price else 0
    veto = total > settings.costa_max_exposure_per_market_krw
    score = 75.0 if not veto else 40.0
    warnings = []
    if not settings.enable_costa_dca:
        warnings.append("CostA DCA disabled; no additional buy intent will be generated")
    if veto:
        warnings.append("max exposure exceeded")
    return PersonaResult(
        persona_name="CostA",
        market=market,
        score=score,
        decision=decision_from_score(score, 60),
        reasons=[f"planned max exposure {total:.0f} KRW", f"escape price {escape_price:.4f}"],
        warnings=warnings,
        veto=False,
        payload={"buy_plan": steps, "avg_price_after_steps": avg_price, "escape_price": escape_price, "dca_enabled": settings.enable_costa_dca},
    )
