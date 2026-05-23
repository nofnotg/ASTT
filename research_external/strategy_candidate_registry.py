from __future__ import annotations

import json
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ROOT_DIR
from research_external.strategy_spec_schema import validate_strategy_spec


STRATEGIES = [
    {
        "strategy_id": "ext_vwap_pullback_scalp_001",
        "name": "VWAP Pullback Scalp",
        "source_id": "manual_public_pattern",
        "source_url": "manual",
        "license_status": "OK",
        "strategy_family": "scalp",
        "timeframes": ["5m", "1m", "seconds"],
        "indicators": [{"name": "VWAP", "params": {}, "role": "trigger"}, {"name": "volume_spike", "params": {"lookback": 20}, "role": "filter"}, {"name": "second_candle_acceleration", "params": {"seconds": 5}, "role": "trigger"}, {"name": "spread", "params": {}, "role": "risk"}],
        "entry_rules": ["price_above_vwap", "pullback_reclaims_vwap", "volume_expands", "micro_buy_pressure_confirms"],
        "exit_rules": ["fixed_rr_1_2", "micro_failure_exit"],
        "risk_rules": ["spread_cost_to_target_below_30pct", "btc_shock_block"],
        "market_regime_rules": ["avoid_btc_micro_shock"],
        "micro_execution_required": True,
        "notes": ["ASTT reimplementation of a common public VWAP pullback structure; no code copied."],
    },
    {
        "strategy_id": "ext_opening_range_breakout_001",
        "name": "Opening Range Breakout",
        "source_id": "manual_public_pattern",
        "source_url": "manual",
        "license_status": "OK",
        "strategy_family": "breakout",
        "timeframes": ["5m", "1m", "seconds"],
        "indicators": [{"name": "range_high_low", "params": {"minutes": 15}, "role": "trigger"}, {"name": "ATR", "params": {"period": 14}, "role": "risk"}, {"name": "volume_spike", "params": {}, "role": "filter"}],
        "entry_rules": ["initial_range_forms", "range_high_breaks", "micro_breakout_holds"],
        "exit_rules": ["false_breakout_cancel", "fixed_rr_1_5"],
        "risk_rules": ["atr_stop", "micro_failure_exit"],
        "market_regime_rules": ["btc_shock_block"],
        "micro_execution_required": True,
        "notes": ["Uses the Korean 09:00 open as one possible range anchor, but does not force entry."],
    },
    {
        "strategy_id": "ext_bollinger_squeeze_breakout_001",
        "name": "Bollinger Squeeze Breakout",
        "source_id": "ta_lib_functions",
        "source_url": "https://ta-lib.github.io/ta-lib-python/funcs.html",
        "license_status": "OK",
        "strategy_family": "breakout",
        "timeframes": ["15m", "5m", "1m", "seconds"],
        "indicators": [{"name": "Bollinger Bands", "params": {"period": 20, "stddev": 2}, "role": "filter"}, {"name": "ATR", "params": {"period": 14}, "role": "risk"}, {"name": "volume_spike", "params": {}, "role": "trigger"}],
        "entry_rules": ["band_width_contracts", "close_breaks_upper_band", "micro_breakout_holds"],
        "exit_rules": ["fixed_rr_1_2", "micro_failure_exit"],
        "risk_rules": ["avoid_wide_spread"],
        "market_regime_rules": ["btc_shock_block"],
        "micro_execution_required": True,
        "notes": ["Indicator taxonomy only; strategy rules are ASTT-authored."],
    },
    {
        "strategy_id": "ext_ema_trend_pullback_001",
        "name": "EMA Trend Pullback",
        "source_id": "manual_public_pattern",
        "source_url": "manual",
        "license_status": "OK",
        "strategy_family": "pullback",
        "timeframes": ["4h", "15m", "5m", "1m", "seconds"],
        "indicators": [{"name": "EMA", "params": {"periods": [20, 50, 100]}, "role": "filter"}, {"name": "ATR", "params": {"period": 14}, "role": "risk"}, {"name": "volume", "params": {}, "role": "filter"}],
        "entry_rules": ["higher_timeframe_ema_aligned", "m5_pullback_holds", "m1_reaccelerates"],
        "exit_rules": ["fixed_rr_1_5", "swing_low_stop"],
        "risk_rules": ["stop_below_recent_swing_low"],
        "market_regime_rules": ["btc_shock_block"],
        "micro_execution_required": True,
        "notes": ["Keeps the V5 Daily+4H lesson but converts entry to micro confirmation."],
    },
    {
        "strategy_id": "ext_rsi_mean_reversion_scalp_001",
        "name": "RSI Mean Reversion Scalp",
        "source_id": "ta_lib_functions",
        "source_url": "https://ta-lib.github.io/ta-lib-python/funcs.html",
        "license_status": "OK",
        "strategy_family": "mean_reversion",
        "timeframes": ["5m", "1m", "seconds"],
        "indicators": [{"name": "RSI", "params": {"period": 14}, "role": "trigger"}, {"name": "VWAP", "params": {}, "role": "filter"}, {"name": "ATR", "params": {"period": 14}, "role": "risk"}],
        "entry_rules": ["rsi_recovers_from_oversold", "price_reclaims_vwap_or_midline", "micro_bounce_confirms"],
        "exit_rules": ["quick_reversion_target", "micro_failure_exit"],
        "risk_rules": ["btc_risk_off_block"],
        "market_regime_rules": ["avoid_risk_off"],
        "micro_execution_required": True,
        "notes": ["Mean reversion is paper-only until cost survival is proven."],
    },
    {
        "strategy_id": "ext_donchian_breakout_001",
        "name": "Donchian Breakout",
        "source_id": "ta_lib_functions",
        "source_url": "https://ta-lib.github.io/ta-lib-python/funcs.html",
        "license_status": "OK",
        "strategy_family": "breakout",
        "timeframes": ["15m", "5m", "1m", "seconds"],
        "indicators": [{"name": "Donchian Channel", "params": {"period": 20}, "role": "trigger"}, {"name": "volume_spike", "params": {}, "role": "filter"}],
        "entry_rules": ["recent_high_breaks", "volume_confirms", "micro_false_breakout_not_detected"],
        "exit_rules": ["fixed_rr_1_5", "micro_failure_exit"],
        "risk_rules": ["spread_guard"],
        "market_regime_rules": ["btc_shock_block"],
        "micro_execution_required": True,
        "notes": ["False breakout defense is mandatory."],
    },
    {
        "strategy_id": "ext_orderbook_imbalance_scalp_001",
        "name": "Orderbook Imbalance Scalp",
        "source_id": "manual_public_pattern",
        "source_url": "manual",
        "license_status": "REVIEW_REQUIRED",
        "strategy_family": "scalp",
        "timeframes": ["seconds"],
        "indicators": [{"name": "orderbook_imbalance", "params": {}, "role": "trigger"}, {"name": "spread", "params": {}, "role": "risk"}, {"name": "trade_aggressor_ratio", "params": {"seconds": 5}, "role": "trigger"}],
        "entry_rules": ["bid_ask_size_ratio_supports_long", "buy_aggressor_ratio_confirms", "spread_tight"],
        "exit_rules": ["very_short_time_stop", "micro_failure_exit"],
        "risk_rules": ["orderbook_unavailable_block"],
        "market_regime_rules": ["btc_micro_shock_block"],
        "micro_execution_required": True,
        "notes": ["Requires real orderbook coverage; REST seconds alone is insufficient."],
    },
]


def build_external_strategy_registry(output_dir: Path | None = None) -> dict:
    out_dir = output_dir or REPLAY_STORE_DIR / "reports" / "open_strategy"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [{**spec, "validation": validate_strategy_spec(spec)} for spec in STRATEGIES]
    result = {
        "source_count": 5,
        "strategy_specs_created": len(rows),
        "license_review_required_count": sum(1 for spec in rows if spec["license_status"] == "REVIEW_REQUIRED"),
        "do_not_use_count": sum(1 for spec in rows if spec["license_status"] == "DO_NOT_USE"),
        "strategies": rows,
    }
    (out_dir / "external_strategy_registry.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    docs = ROOT_DIR / "docs" / "reports"
    docs.mkdir(parents=True, exist_ok=True)
    return result


def get_initial_strategy_specs() -> list[dict]:
    return [dict(spec) for spec in STRATEGIES]
