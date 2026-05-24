from __future__ import annotations

from live_capture.volatility_trigger_detector import detect_btc_shock


def summarize_btc_context(btc_1m_change_pct: float = 0.0) -> dict:
    shock = detect_btc_shock(btc_1m_change_pct)
    return {"btc_1m_change_pct": btc_1m_change_pct, "btc_shock": shock["triggered"], "btc_micro_state": "SHOCK" if shock["triggered"] else "STABLE"}
