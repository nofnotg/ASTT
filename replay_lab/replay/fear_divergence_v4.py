from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from execution.skeptic_guard import evaluate_skeptic_guard
from features.bollinger_reentry import compute_bollinger, detect_lower_band_reentry
from features.divergence import detect_bullish_fear_divergence
from features.fear_oscillator import compute_fear_oscillator
from features.support_resistance import body_zone_context, moving_average_context
from features.trendline import detect_trendline_bounce
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import aggregate_small_seed_daily, aggregate_small_seed_monthly, aggregate_small_seed_weekly, calc_trade_pnl, summarize_trades


@dataclass(frozen=True)
class FearDivergenceConfig:
    timeframe: str = "5m"
    lookback: int = 30
    bollinger_length: int = 30
    bollinger_stddev: float = 2.0
    min_divergence_strength: float = 60.0
    min_v4_score: float = 70.0
    min_body_zone_score: float = 40.0
    min_trendline_score: float = 40.0
    exit_mode: str = "middle_band"
    max_hold_minutes: int = 90


def run_fear_divergence_v4(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    timeframe: str = "5m",
    top_markets: int = 50,
    config: FearDivergenceConfig | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    config = config or FearDivergenceConfig(timeframe=timeframe)
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_fear_divergence_v4")
    exp_dir = store_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    selected_markets = markets[:top_markets] if top_markets else markets
    candidates, trades = scan_fear_divergence_v4(start_date, end_date, selected_markets, capital_krw, order_krw, config, store_dir)
    daily = aggregate_small_seed_daily(trades.to_dict("records"), capital_krw)
    weekly = aggregate_small_seed_weekly(daily, capital_krw)
    monthly = aggregate_small_seed_monthly(daily, capital_krw)
    summary = {
        **summarize_trades(trades.to_dict("records"), capital_krw),
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "timeframe": timeframe,
        "skeptic_guard_active": True,
        "skeptic_reject_count": int((candidates.get("skeptic_decision", pd.Series(dtype=str)) == "REJECT").sum()) if not candidates.empty else 0,
        "candidate_count": int(len(candidates)),
        "live_readiness": live_readiness_v4(summarize_trades(trades.to_dict("records"), capital_krw), True),
    }
    config_payload = {
        "experiment_id": experiment_id,
        "mode": "FEAR_DIVERGENCE_V4",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "markets": selected_markets,
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        **asdict(config),
    }
    (exp_dir / "config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    candidates.to_parquet(exp_dir / "candidates.parquet", index=False)
    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    daily.to_parquet(exp_dir / "daily_account.parquet", index=False)
    weekly.to_parquet(exp_dir / "weekly_account.parquet", index=False)
    monthly.to_parquet(exp_dir / "monthly_account.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (exp_dir / "report.md").write_text(_markdown(summary), encoding="utf-8")
    return exp_dir


def scan_fear_divergence_v4(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float,
    order_krw: float,
    config: FearDivergenceConfig,
    store_dir: Path = REPLAY_STORE_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidate_rows: list[dict[str, Any]] = []
    trade_rows: list[dict[str, Any]] = []
    for market in markets:
        frame = _load_timeframe_frame(store_dir, market, config.timeframe)
        if frame.empty:
            continue
        frame = frame[(frame["time"] >= pd.Timestamp(start_date)) & (frame["time"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))]
        if len(frame) < max(config.lookback, config.bollinger_length) + 2:
            continue
        enriched = compute_fear_oscillator(frame, config.lookback)
        enriched = compute_bollinger(enriched, config.bollinger_length, config.bollinger_stddev)
        start_index = max(config.lookback, config.bollinger_length, 60)
        for idx in range(start_index, len(enriched) - 2):
            now = pd.Timestamp(enriched.iloc[idx]["time"])
            if now.date() < start_date or now.date() > end_date:
                continue
            current = enriched.iloc[idx]
            lower_band = float(current.get("lower_band", 0.0) or 0.0)
            if float(current.get("fear_score", 0.0)) < 60.0:
                continue
            if lower_band and float(current["low"]) > lower_band * 1.005:
                continue
            window = enriched.iloc[max(0, idx - config.lookback + 1) : idx + 1].copy()
            candidate = evaluate_v4_candidate(window, market, config)
            if not candidate["is_candidate"]:
                continue
            candidate["date_kst"] = now.date().isoformat()
            candidate["signal_time_kst"] = now.isoformat()
            candidate["market"] = market
            guard = candidate["skeptic"]
            row = _flatten_candidate(candidate)
            candidate_rows.append(row)
            if guard["skeptic_decision"] == "PASS":
                trade = _simulate_trade(enriched, idx + 1, market, now, candidate, capital_krw, order_krw, config)
                if trade:
                    trade_rows.append(trade)
    candidates = pd.DataFrame(candidate_rows)
    trades = pd.DataFrame(trade_rows)
    if not trades.empty:
        trades = trades.sort_values(["date_kst", "signal_time_kst", "v4_score"], ascending=[True, True, False]).groupby("date_kst", as_index=False).head(1)
    return candidates, trades


def evaluate_v4_candidate(window: pd.DataFrame, market: str, config: FearDivergenceConfig) -> dict:
    divergence = detect_bullish_fear_divergence(window, min_price_lower_low_pct=0.3, max_fear_peak_ratio=0.9)
    bollinger = detect_lower_band_reentry(window, config.bollinger_length, config.bollinger_stddev)
    ma = moving_average_context(window)
    body = body_zone_context(window, float(window.iloc[-1]["close"]) if not window.empty else 0.0)
    trendline = detect_trendline_bounce(window)
    liquidity = _liquidity_context(window)
    risk = _risk_context(window)
    v4_score = (
        divergence["divergence_strength"] * 0.30
        + bollinger["reentry_strength"] * 0.20
        + body["body_zone_score"] * 0.20
        + trendline["trendline_score"] * 0.15
        + ma["ma_context_score"] * 0.10
        + liquidity["liquidity_score"] * 0.05
    )
    min_support = body["body_zone_score"] >= config.min_body_zone_score or trendline["trendline_score"] >= config.min_trendline_score
    target_space = body["target_space_pct"]
    is_candidate = (
        divergence["divergence_strength"] >= config.min_divergence_strength
        and bollinger["reentered_lower_band"]
        and min_support
        and target_space >= 0.6
        and v4_score >= config.min_v4_score
    )
    guard_input = {
        "strategy": "FEAR_DIVERGENCE_V4",
        "market": market,
        "timeframe": config.timeframe,
        "v4_score": v4_score,
        "divergence": divergence,
        "bollinger": bollinger,
        "ma_context": ma,
        "body_zone": body,
        "trendline": trendline,
        "liquidity": liquidity,
        "btc_context": {"btc_drop_pct": 0.0},
        "risk": risk,
    }
    skeptic = evaluate_skeptic_guard(guard_input) if is_candidate else {"skeptic_decision": "REJECT", "skeptic_score": 0.0, "reject_reasons": ["minimum_conditions_failed"], "warnings": [], "required_confirmation": []}
    return {
        "is_candidate": bool(is_candidate),
        "v4_score": float(v4_score),
        "divergence": divergence,
        "bollinger": bollinger,
        "ma_context": ma,
        "body_zone": body,
        "trendline": trendline,
        "liquidity": liquidity,
        "risk": risk,
        "skeptic": skeptic,
    }


def live_readiness_v4(metrics: dict, skeptic_guard_active: bool) -> str:
    if (
        metrics.get("entry_count", 0) >= 30
        and metrics.get("win_rate", 0.0) >= 0.50
        and metrics.get("profit_factor", 0.0) >= 1.2
        and metrics.get("account_return_pct", 0.0) > 0
        and metrics.get("max_drawdown_pct", 0.0) >= -8.0
        and metrics.get("consecutive_loss_max", 999) <= 3
        and skeptic_guard_active
    ):
        return "MICRO_LIVE_READY"
    if metrics.get("entry_count", 0) >= 10:
        return "PAPER_MORE_REQUIRED"
    return "LIVE_NOT_ALLOWED"


def latest_fear_divergence_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    experiments = sorted((store_dir / "experiments").glob("exp_*_fear_divergence_v4"), key=lambda path: path.name)
    return experiments[-1] if experiments else None


def _simulate_trade(frame: pd.DataFrame, entry_idx: int, market: str, signal_time: pd.Timestamp, candidate: dict, capital_krw: float, order_krw: float, config: FearDivergenceConfig) -> dict | None:
    if entry_idx >= len(frame):
        return None
    entry_time = pd.Timestamp(frame.iloc[entry_idx]["time"])
    max_end = entry_time + pd.Timedelta(minutes=config.max_hold_minutes)
    outcome = frame[(frame["time"] >= entry_time) & (frame["time"] <= max_end)].copy()
    if outcome.empty:
        return None
    signal_price = float(outcome.iloc[0]["open"])
    stop = min(float(candidate["divergence"].get("price_low_2", signal_price * 0.99)), signal_price * 0.994)
    if config.exit_mode == "ma30":
        take_profit = max(signal_price * 1.006, float(candidate["ma_context"].get("ma30", signal_price * 1.006)))
    elif config.exit_mode == "fixed_rr":
        take_profit = signal_price + (signal_price - stop) * 1.2
    else:
        take_profit = max(signal_price * 1.006, float(candidate["bollinger"].get("middle_band", signal_price * 1.006)))
    fill = simulate_long_trade(outcome, signal_price, stop, take_profit, fee_pct=0.0, slippage_pct=0.0)
    pnl = calc_trade_pnl(capital_krw, order_krw, fill.pnl_pct, fee_pct=0.0, slippage_pct=0.0)
    hold_minutes = (pd.Timestamp(outcome.iloc[-1]["time"]) - entry_time).total_seconds() / 60
    return {
        "date_kst": signal_time.date().isoformat(),
        "market": market,
        "signal_time_kst": signal_time.isoformat(),
        "entry_time_kst": entry_time.isoformat(),
        "exit_reason": fill.exit_reason,
        "entry_price": fill.entry_price,
        "exit_price": fill.exit_price,
        "v4_score": candidate["v4_score"],
        "divergence_strength": candidate["divergence"]["divergence_strength"],
        "body_zone_score": candidate["body_zone"]["body_zone_score"],
        "trendline_score": candidate["trendline"]["trendline_score"],
        "reentry_strength": candidate["bollinger"]["reentry_strength"],
        "ma_context_score": candidate["ma_context"]["ma_context_score"],
        "liquidity_score": candidate["liquidity"]["liquidity_score"],
        "skeptic_decision": candidate["skeptic"]["skeptic_decision"],
        "hold_minutes": hold_minutes,
        "entered": True,
        **pnl,
    }


def _flatten_candidate(candidate: dict) -> dict:
    return {
        "date_kst": candidate.get("date_kst"),
        "signal_time_kst": candidate.get("signal_time_kst"),
        "market": candidate.get("market"),
        "v4_score": candidate["v4_score"],
        "divergence_strength": candidate["divergence"]["divergence_strength"],
        "reentry_strength": candidate["bollinger"]["reentry_strength"],
        "body_zone_score": candidate["body_zone"]["body_zone_score"],
        "trendline_score": candidate["trendline"]["trendline_score"],
        "ma_context_score": candidate["ma_context"]["ma_context_score"],
        "liquidity_score": candidate["liquidity"]["liquidity_score"],
        "target_space_pct": candidate["body_zone"]["target_space_pct"],
        "skeptic_decision": candidate["skeptic"]["skeptic_decision"],
        "skeptic_score": candidate["skeptic"]["skeptic_score"],
        "reject_reasons": "|".join(candidate["skeptic"].get("reject_reasons", [])),
        "warnings": "|".join(candidate["skeptic"].get("warnings", [])),
    }


def _liquidity_context(window: pd.DataFrame) -> dict:
    if window.empty:
        return {"liquidity_score": 0.0, "value_ratio": 0.0}
    value = window["trade_price"].astype(float) if "trade_price" in window else window["close"].astype(float) * window["volume"].astype(float)
    recent = float(value.tail(6).mean())
    base = float(value.mean()) if float(value.mean()) else 1.0
    ratio = recent / base
    return {"liquidity_score": max(0.0, min(100.0, ratio * 45)), "value_ratio": ratio}


def _risk_context(window: pd.DataFrame) -> dict:
    if window.empty:
        return {"falling_knife_speed_pct": 0.0, "close_position": 1.0}
    recent = window.tail(6)
    start = float(recent.iloc[0]["open"])
    end = float(recent.iloc[-1]["close"])
    speed = (end - start) / start * 100 if start else 0.0
    current = window.iloc[-1]
    rng = float(current["high"]) - float(current["low"])
    close_position = (float(current["close"]) - float(current["low"])) / rng if rng else 1.0
    return {"falling_knife_speed_pct": speed, "close_position": close_position}


def _load_timeframe_frame(store_dir: Path, market: str, timeframe: str) -> pd.DataFrame:
    path = store_dir / "normalized" / "candles_1m" / f"{market}.parquet"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame["time"] = pd.to_datetime(frame["candle_time_kst"])
    frame = frame.sort_values("time")
    if timeframe == "1m":
        return frame[["time", "open", "high", "low", "close", "volume", "trade_price"]].copy()
    if timeframe != "5m":
        raise ValueError("V4 currently supports 1m or 5m replay frames")
    indexed = frame.set_index("time")
    resampled = indexed.resample("5min").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "trade_price": "sum"}).dropna().reset_index()
    return resampled


def _markdown(metrics: dict) -> str:
    return f"""# Fear Divergence V4 Result

- entry_count: {metrics.get("entry_count", 0)}
- win_rate: {metrics.get("win_rate", 0) * 100:.2f}%
- profit_factor: {metrics.get("profit_factor", 0):.4f}
- account_return_pct: {metrics.get("account_return_pct", 0):.4f}%
- max_drawdown_pct: {metrics.get("max_drawdown_pct", 0):.4f}%
- consecutive_loss_max: {metrics.get("consecutive_loss_max", 0)}
- skeptic_reject_count: {metrics.get("skeptic_reject_count", 0)}
- live_readiness: {metrics.get("live_readiness")}
"""
