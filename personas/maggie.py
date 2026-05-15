from __future__ import annotations

from features.body_zone import calculate_body_zones, detect_rs_flip, target_space_pct
from personas.base import PersonaResult, decision_from_score


def analyze(context: dict) -> PersonaResult:
    market = context.get("market", "KRW-BTC")
    df = context.get("candles")
    zones_data = calculate_body_zones(df)
    zone = zones_data.get("zones", [{}])[-1] if zones_data.get("zones") else None
    rs = detect_rs_flip(df, zone)
    current = float(df["close"].iloc[-1]) if df is not None and not df.empty else 0.0
    recent_high = float(df["high"].tail(20).max()) if df is not None and not df.empty else current
    space = target_space_pct(current, recent_high)
    score = 40.0
    reasons = []
    warnings = []
    if zone:
        score += 20
        reasons.append("heavy-volume body zone exists")
    else:
        warnings.append("no heavy-volume body zone")
    if rs["state"] in {"PRE_BREAKOUT", "BREAKOUT", "RETEST"}:
        score += 20
        reasons.append(f"R/S flip state {rs['state']}")
    if space >= 1.5:
        score += 15
        reasons.append(f"target space {space:.2f}%")
    else:
        warnings.append(f"target space is low: {space:.2f}%")
    if context.get("regime", {}).get("state") != "bearish":
        score += 5
    score = min(100.0, score)
    payload = {
        "entry_zone": zone,
        "stop_loss": current * 0.985 if current else None,
        "target": current * 1.015 if current else None,
        "target_space_pct": space,
        "rs_flip": rs,
    }
    return PersonaResult(
        persona_name="매기",
        market=market,
        score=score,
        decision=decision_from_score(score, 85),
        reasons=reasons or ["candidate position evaluated"],
        warnings=warnings,
        payload=payload,
    )
