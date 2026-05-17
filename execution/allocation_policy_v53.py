from __future__ import annotations


def decide_allocation_v53(
    current_equity_krw: float,
    signal_grade: str,
    target_space_grade: str,
    fractal_state: str,
    btc_regime: str,
    consecutive_loss: int = 0,
) -> dict:
    base = {
        "A_PLUS": 0.90,
        "A": 0.65,
        "B": 0.35,
        "C": 0.08,
        "REJECT": 0.0,
        "PAPER_ONLY": 0.0,
    }.get(signal_grade, 0.0)
    reasons: list[str] = [f"signal_grade={signal_grade}"]
    warnings: list[str] = []
    if target_space_grade == "A_PLUS":
        base = max(base, 0.75)
    elif target_space_grade == "A":
        base = max(base, 0.55)
    elif target_space_grade == "B":
        base = min(base, 0.40)
    elif target_space_grade in {"C", "REJECT"}:
        base = min(base, 0.10 if target_space_grade == "C" else 0.0)
    if fractal_state in {"CONFLICT", "RISK", "LOWER_TIMEFRAME_ONLY"}:
        base *= 0.35
        warnings.append("fractal_conflict_size_cut")
    if btc_regime == "BTC_LED":
        base *= 0.65
        warnings.append("btc_led_size_cut")
    elif btc_regime in {"RISK_OFF", "ALT_RISK_OFF"}:
        base = 0.0
        warnings.append("risk_off_veto")
    elif btc_regime in {"UNCLEAR", "DOMINANCE_UNAVAILABLE"}:
        base *= 0.75
        warnings.append("regime_unclear_size_cut")
    if consecutive_loss >= 2:
        base *= 0.5
        warnings.append("loss_streak_size_cut")
    allocation_pct = max(0.0, min(1.0, base))
    return {
        "current_equity_krw": float(current_equity_krw),
        "allocation_pct": allocation_pct,
        "position_size_krw": float(current_equity_krw) * allocation_pct,
        "signal_grade": signal_grade,
        "reason": reasons,
        "warnings": warnings,
    }
