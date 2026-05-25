from __future__ import annotations

from btcd.btcd_schema import BearRegimeComposite


def detect_global_btcd_regime(delta_7d: float | None, delta_30d: float | None, zscore_90d: float | None) -> str:
    d7 = float(delta_7d or 0.0)
    d30 = float(delta_30d or 0.0)
    z90 = float(zscore_90d or 0.0)
    if z90 >= 1.5 and d7 > 0:
        return "BTCD_SPIKE"
    if d7 >= 0.8 or d30 >= 2.0:
        return "BTCD_RISING"
    if d7 <= -0.8 or d30 <= -2.0:
        return "BTCD_FALLING"
    if z90 <= -1.5 and d7 < 0:
        return "BTCD_BREAKDOWN"
    return "BTCD_STABLE"


def build_bear_composite(
    btcd_regime: str,
    flow_regime: str,
    alt_volume_breadth: float | None,
    strategy_pf: float | None,
    drawdown_pct: float,
    monthly_return_pct: float = 0.0,
) -> BearRegimeComposite:
    score = 0
    reasons: list[str] = []
    breadth = float(alt_volume_breadth or 0.0)
    pf = float(strategy_pf or 1.0)
    if btcd_regime in {"BTCD_RISING", "BTCD_SPIKE"}:
        score += 20 if btcd_regime == "BTCD_RISING" else 30
        reasons.append(btcd_regime)
    if flow_regime in {"BTC_FLOW_RISING", "BTC_FLOW_SPIKE"}:
        score += 20 if flow_regime == "BTC_FLOW_RISING" else 25
        reasons.append(flow_regime)
    if breadth < 0.45:
        score += 15
        reasons.append("ALT_BREADTH_WEAK")
    if pf < 1.0:
        score += 15
        reasons.append("STRATEGY_PF_WEAK")
    if drawdown_pct <= -10.0:
        score += 10
        reasons.append("ACCOUNT_DRAWDOWN")
    if monthly_return_pct <= -3.0:
        score += 10
        reasons.append("MONTHLY_LOSS")

    if score >= 90:
        state = "LOCKDOWN"
    elif score >= 75:
        state = "BEAR_BOUNCE_ONLY"
    elif score >= 60:
        state = "BEAR_DEFENSE"
    elif score >= 35:
        state = "EDGE_DECAY"
    else:
        state = "NORMAL"
    return BearRegimeComposite(bear_transition_score=min(100, score), bear_state=state, reasons=reasons)

