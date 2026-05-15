from __future__ import annotations

from features.cvd import calculate_cvd
from features.rvol import calculate_rvol
from features.vwap import calculate_vwap
from personas.base import PersonaResult, decision_from_score


def analyze(context: dict) -> PersonaResult:
    market = context.get("market", "KRW-BTC")
    candles = context.get("candles")
    trades = context.get("trades")
    rvol = calculate_rvol(candles)
    vwap = calculate_vwap(candles)
    cvd = calculate_cvd(trades)
    warnings = [value for value in [rvol.get("warning"), vwap.get("warning"), cvd.get("warning")] if value]
    score = 35.0
    if rvol.get("rvol", 0) >= 2.5:
        score += 25
    if rvol.get("volume_acceleration", 0) >= 2.0:
        score += 15
    if vwap.get("above_vwap"):
        score += 15
    if cvd.get("direction") == "up":
        score += 10
    if warnings:
        score = min(score, 65)
    reasons = [
        f"RVOL {rvol.get('rvol', 0):.2f}",
        f"volume acceleration {rvol.get('volume_acceleration', 0):.2f}",
        f"CVD direction {cvd.get('direction')}",
    ]
    return PersonaResult(
        persona_name="Rezo",
        market=market,
        score=min(100.0, score),
        decision=decision_from_score(score, 80),
        reasons=reasons,
        warnings=warnings,
        payload={"rvol": rvol, "vwap": vwap, "cvd": cvd},
    )
