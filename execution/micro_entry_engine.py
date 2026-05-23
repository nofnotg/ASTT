from __future__ import annotations


def decide_micro_entry(setup_context: dict, micro_signal: dict, micro_liquidity: dict, risk_context: dict) -> dict:
    veto = []
    warnings = []
    if not setup_context.get("setup_pass", True):
        veto.append("SETUP_NOT_PASS")
    if risk_context.get("btc_shock", False):
        veto.append("BTC_SHOCK")
    if micro_liquidity.get("liquidity_state") in {"WIDE_SPREAD", "THIN", "NO_DATA"}:
        veto.append(micro_liquidity.get("liquidity_state", "LIQUIDITY_BAD"))
    if micro_liquidity.get("spread_pct", 999.0) > 0.25:
        veto.append("SPREAD_TOO_WIDE")
    if micro_signal.get("micro_state") in {"REVERSING"}:
        veto.append("MICRO_REVERSING")
    if veto:
        return {"entry_decision": "CANCEL", "entry_price": 0.0, "entry_type": "PAPER_MARKET", "reason": [], "veto_reasons": veto, "max_slippage_pct": 0.15, "warnings": warnings}
    if micro_signal.get("micro_state") in {"ACCELERATING", "STABLE"} and micro_signal.get("buy_trade_ratio_5s", 0.5) >= 0.55 and micro_signal.get("price_change_5s_pct", 0.0) >= 0:
        price = float(micro_liquidity.get("best_ask_price") or setup_context.get("reference_price", 0.0))
        return {"entry_decision": "ENTER", "entry_price": price, "entry_type": "PAPER_MARKET", "reason": ["micro_momentum_pass", "spread_pass"], "veto_reasons": [], "max_slippage_pct": 0.15, "warnings": warnings}
    return {"entry_decision": "WAIT", "entry_price": 0.0, "entry_type": "PAPER_MARKET", "reason": ["micro_not_ready"], "veto_reasons": [], "max_slippage_pct": 0.15, "warnings": warnings}
