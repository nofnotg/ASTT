from __future__ import annotations


def decide_position_size(current_equity_krw, signal_grade, target_space_grade, fractal_context, btc_dominance_regime, risk_result) -> dict:
    base = {"A_PLUS": 0.9, "A": 0.65, "B": 0.3, "C": 0.08, "REJECT": 0.0}.get(signal_grade, 0.0)
    if target_space_grade == "REJECT" or risk_result.get("risk_decision") == "REJECT" or not btc_dominance_regime.get("alt_long_allowed", True):
        base = 0.0
    mult = float(btc_dominance_regime.get("position_size_multiplier", 1.0))
    if target_space_grade == "C":
        mult *= 0.2
    if fractal_context.get("fractal_state") in {"CONFLICT", "LOWER_TIMEFRAME_ONLY"}:
        mult *= 0.5
    if fractal_context.get("recommended_mode") == "NO_TRADE":
        mult = 0.0
    allocation = max(0.0, min(1.0, base * mult))
    max_allowed = float(risk_result.get("max_allowed_allocation_pct", 1.0))
    allocation = min(allocation, max_allowed)
    return {"current_equity_krw": float(current_equity_krw), "allocation_pct": allocation, "position_size_krw": float(current_equity_krw) * allocation, "signal_grade": signal_grade, "reason": [signal_grade, target_space_grade, btc_dominance_regime.get("alt_regime", "")], "warnings": []}
