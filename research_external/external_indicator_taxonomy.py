from __future__ import annotations


INDICATORS = {
    "ema": ("Trend", [20, 50, 100], "trend_confirmation", "filter"),
    "sma": ("Trend", [20, 50, 100], "trend_confirmation", "filter"),
    "macd": ("Trend", [12, 26, 9], "momentum_confirmation", "filter"),
    "adx": ("Trend", [14], "trend_strength", "filter"),
    "supertrend": ("Trend", [10, 3], "trend_following", "filter"),
    "rsi": ("Momentum", [14, 7, 21], "overbought_oversold", "trigger"),
    "stochastic": ("Momentum", [14, 3, 3], "momentum_reversal", "trigger"),
    "cci": ("Momentum", [20], "mean_reversion", "trigger"),
    "roc": ("Momentum", [12], "momentum_confirmation", "trigger"),
    "atr": ("Volatility", [14], "stop_and_position_risk", "risk"),
    "bollinger_bands": ("Volatility", [20, 2], "squeeze_or_reversion", "trigger"),
    "keltner_channel": ("Volatility", [20, 2], "volatility_breakout", "trigger"),
    "donchian_channel": ("Volatility", [20, 55], "breakout", "trigger"),
    "obv": ("Volume / Flow", [20], "volume_confirmation", "filter"),
    "mfi": ("Volume / Flow", [14], "money_flow_reversal", "trigger"),
    "volume_spike": ("Volume / Flow", [20, 2], "participation_expansion", "trigger"),
    "vwap": ("Volume / Flow", [], "intraday_fair_value", "trigger"),
    "cvd_proxy": ("Volume / Flow", [10], "aggressor_flow", "trigger"),
    "btc_trend": ("Market Regime", [5, 15, 60], "risk_filter", "risk"),
    "btc_dominance": ("Market Regime", [60, 240], "alt_regime", "risk"),
    "market_breadth": ("Market Regime", [30], "market_health", "risk"),
    "volatility_regime": ("Market Regime", [20], "risk_filter", "risk"),
    "spread": ("Microstructure", [1], "execution_cost", "risk"),
    "orderbook_imbalance": ("Microstructure", [1], "liquidity_pressure", "trigger"),
    "trade_aggressor_ratio": ("Microstructure", [5, 10], "buy_sell_pressure", "trigger"),
    "second_candle_acceleration": ("Microstructure", [3, 5, 10], "micro_momentum", "trigger"),
}


def build_indicator_taxonomy() -> list[dict]:
    return [
        {
            "indicator_id": indicator_id,
            "group": group,
            "parameters": parameters,
            "expected_use": expected_use,
            "astt_role": astt_role,
        }
        for indicator_id, (group, parameters, expected_use, astt_role) in sorted(INDICATORS.items())
    ]


def classify_indicator(indicator_id: str) -> dict:
    key = indicator_id.lower().replace(" ", "_")
    if key not in INDICATORS:
        return {"indicator_id": key, "group": "Unknown", "parameters": [], "expected_use": "review_required", "astt_role": "filter"}
    group, parameters, expected_use, astt_role = INDICATORS[key]
    return {"indicator_id": key, "group": group, "parameters": parameters, "expected_use": expected_use, "astt_role": astt_role}
