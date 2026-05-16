from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from execution.skeptic_guard import evaluate_skeptic_guard
from features.bollinger_reentry import compute_bollinger, detect_lower_band_reentry
from features.fear_oscillator import compute_fear_oscillator
from features.relaxed_exhaustion import detect_drop_event, detect_fear_cooling, detect_low_retest_or_lower_low, evaluate_min_support_context
from features.support_resistance import body_zone_context, moving_average_context
from features.trendline import detect_trendline_bounce
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_divergence_v4 import _liquidity_context, _load_timeframe_frame, _risk_context
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import aggregate_small_seed_daily, aggregate_small_seed_monthly, aggregate_small_seed_weekly, calc_trade_pnl, summarize_trades


@dataclass(frozen=True)
class FearExhaustionV41Config:
    timeframe: str = "1m"
    lookback: int = 24
    min_drop_pct: float = 0.7
    low_tolerance_pct: float = 0.5
    cooling_ratio: float = 0.95
    bollinger_length: int = 20
    bollinger_stddev: float = 2.0
    min_support_score: float = 30.0
    min_v41_score: float = 65.0
    exit_mode: str = "middle_band"
    max_hold_minutes: int = 60
    skeptic_guard_mode: str = "DIAGNOSTIC"
    blocking_enabled: bool = False


def default_min_drop_pct(timeframe: str) -> float:
    return 0.7 if timeframe == "1m" else 1.2


def run_fear_exhaustion_v41(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float = 500000,
    order_krw: float = 10000,
    timeframe: str = "1m",
    top_markets: int = 50,
    config: FearExhaustionV41Config | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    config = config or FearExhaustionV41Config(timeframe=timeframe, min_drop_pct=default_min_drop_pct(timeframe))
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_fear_exhaustion_v41")
    exp_dir = store_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    candidates, trades, funnel = scan_fear_exhaustion_v41(start_date, end_date, markets[:top_markets], capital_krw, order_krw, config, store_dir)
    daily = aggregate_small_seed_daily(trades.to_dict("records"), capital_krw)
    weekly = aggregate_small_seed_weekly(daily, capital_krw)
    monthly = aggregate_small_seed_monthly(daily, capital_krw)
    metrics = {
        **summarize_trades(trades.to_dict("records"), capital_krw),
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "timeframe": timeframe,
        "candidate_count": int(len(candidates)),
        "funnel": funnel,
        "skeptic_guard_mode": config.skeptic_guard_mode,
        "blocking_enabled": config.blocking_enabled,
        "skeptic_would_block_count": int(candidates.get("would_block", pd.Series(dtype=bool)).astype(bool).sum()) if not candidates.empty else 0,
        "blocking_applied_count": int(candidates.get("blocking_applied", pd.Series(dtype=bool)).astype(bool).sum()) if not candidates.empty else 0,
    }
    metrics["live_readiness"] = live_readiness_v41(metrics)
    (exp_dir / "config.json").write_text(json.dumps({"experiment_id": experiment_id, "mode": "FEAR_EXHAUSTION_V41", "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "markets": markets[:top_markets], **asdict(config)}, ensure_ascii=False, indent=2), encoding="utf-8")
    candidates.to_parquet(exp_dir / "candidates.parquet", index=False)
    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    daily.to_parquet(exp_dir / "daily_account.parquet", index=False)
    weekly.to_parquet(exp_dir / "weekly_account.parquet", index=False)
    monthly.to_parquet(exp_dir / "monthly_account.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def scan_fear_exhaustion_v41(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float,
    order_krw: float,
    config: FearExhaustionV41Config,
    store_dir: Path = REPLAY_STORE_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    all_candidates: list[dict[str, Any]] = []
    all_trades: list[dict[str, Any]] = []
    funnel = _empty_funnel(config.timeframe)
    for market in markets:
        frame = _load_timeframe_frame(store_dir, market, config.timeframe)
        if frame.empty:
            continue
        frame = frame[(frame["time"] >= pd.Timestamp(start_date)) & (frame["time"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))]
        if len(frame) < max(config.lookback, config.bollinger_length) + 2:
            continue
        enriched = compute_bollinger(compute_fear_oscillator(frame, config.lookback), config.bollinger_length, config.bollinger_stddev)
        start_idx = max(config.lookback, config.bollinger_length, 30)
        in_period = (enriched["time"] >= pd.Timestamp(start_date)) & (enriched["time"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))
        prefilter = _signal_prefilter(enriched, start_idx) & in_period
        candidate_indices = [idx for idx in enriched.index[prefilter].tolist() if start_idx <= idx < len(enriched) - 2]
        funnel["total_bars"] += int(in_period.iloc[start_idx : max(start_idx, len(enriched) - 2)].sum())
        for idx in candidate_indices:
            now = pd.Timestamp(enriched.iloc[idx]["time"])
            window = enriched.iloc[max(0, idx - config.lookback + 1) : idx + 1].copy()
            candidate = evaluate_v41_candidate(window, market, config)
            _update_funnel(funnel, candidate)
            if not candidate["has_drop_event"]:
                continue
            if not candidate["has_low_structure"]:
                continue
            if not candidate["has_fear_cooling"]:
                continue
            if not candidate["reentered_lower_band"]:
                continue
            if not candidate["has_min_support"]:
                continue
            if not candidate["score_pass"]:
                continue
            candidate["date_kst"] = now.date().isoformat()
            candidate["signal_time_kst"] = now.isoformat()
            candidate["timeframe"] = config.timeframe
            row = _flatten_candidate(candidate)
            all_candidates.append(row)
            if not candidate["blocking_applied"]:
                trade = _simulate_trade(enriched, idx + 1, market, now, candidate, capital_krw, order_krw, config)
                if trade:
                    all_trades.append(trade)
                    funnel["final_entry_count"] += 1
    candidates = pd.DataFrame(all_candidates)
    trades = pd.DataFrame(all_trades)
    if not trades.empty:
        trades = trades.sort_values(["date_kst", "signal_time_kst", "v41_score"], ascending=[True, True, False]).groupby("date_kst", as_index=False).head(1)
        funnel["final_entry_count"] = int(len(trades))
    return candidates, trades, funnel


def _signal_prefilter(frame: pd.DataFrame, start_idx: int) -> pd.Series:
    lower = frame["lower_band"].astype(float)
    fear = frame["fear_score"].astype(float)
    close = frame["close"].astype(float)
    low = frame["low"].astype(float)
    recent_break = pd.Series(False, index=frame.index)
    for offset in range(1, 6):
        recent_break = recent_break | (low.shift(offset) < lower.shift(offset))
    mask = (fear >= 30) & recent_break & (close > lower) & (low <= lower * 1.03)
    mask.iloc[:start_idx] = False
    return mask.fillna(False)


def evaluate_v41_candidate(window: pd.DataFrame, market: str, config: FearExhaustionV41Config) -> dict:
    drop = detect_drop_event(window, config.lookback, config.min_drop_pct)
    low = detect_low_retest_or_lower_low(window, tolerance_pct=config.low_tolerance_pct)
    cooling = detect_fear_cooling(window, cooling_ratio=config.cooling_ratio)
    bollinger = detect_lower_band_reentry(window, config.bollinger_length, config.bollinger_stddev, lookback=5)
    body = body_zone_context(window, float(window.iloc[-1]["close"]) if not window.empty else 0.0)
    trend = detect_trendline_bounce(window)
    ma = moving_average_context(window)
    support = evaluate_min_support_context(window, body, trend, ma, bollinger)
    liquidity = _liquidity_context(window)
    risk = _risk_context(window)
    v41_score = (
        drop["drop_speed_score"] * 0.15
        + low["low_structure_score"] * 0.15
        + cooling["cooling_score"] * 0.25
        + bollinger["reentry_strength"] * 0.20
        + support["support_context_score"] * 0.15
        + liquidity["liquidity_score"] * 0.10
    )
    score_pass = v41_score >= config.min_v41_score and support["support_context_score"] >= config.min_support_score
    guard_input = {
        "strategy": "FEAR_EXHAUSTION_V41",
        "market": market,
        "timeframe": config.timeframe,
        "v4_score": v41_score,
        "divergence": {"divergence_strength": max(low["low_structure_score"], cooling["cooling_score"])},
        "bollinger": bollinger,
        "body_zone": {**body, "body_zone_score": support["support_context_score"], "target_space_pct": support["target_space_pct"]},
        "trendline": trend,
        "liquidity": liquidity,
        "btc_context": {"btc_drop_pct": 0.0},
        "risk": risk,
    }
    skeptic = evaluate_skeptic_guard(guard_input, mode=config.skeptic_guard_mode, blocking_enabled=config.blocking_enabled)
    return {
        "market": market,
        "v41_score": float(v41_score),
        "has_drop_event": drop["has_drop_event"],
        "has_low_structure": low["pattern"] != "NONE",
        "has_fear_cooling": cooling["has_fear_cooling"],
        "reentered_lower_band": bollinger["reentered_lower_band"],
        "has_min_support": support["has_min_support"],
        "score_pass": bool(score_pass),
        "drop": drop,
        "low": low,
        "cooling": cooling,
        "bollinger": bollinger,
        "support": support,
        "body": body,
        "trendline": trend,
        "ma": ma,
        "liquidity": liquidity,
        "risk": risk,
        "skeptic": skeptic,
        "skeptic_decision": skeptic["skeptic_decision"],
        "would_block": skeptic["would_block"],
        "blocking_applied": skeptic["blocking_applied"],
    }


def live_readiness_v41(metrics: dict) -> str:
    if metrics.get("entry_count", 0) < 30:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("account_return_pct", 0.0) <= 0 or metrics.get("profit_factor", 0.0) < 1.0 or metrics.get("consecutive_loss_max", 0) > 4:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("profit_factor", 0.0) >= 1.1 and metrics.get("max_drawdown_pct", 0.0) >= -8.0:
        return "MICRO_LIVE_READY"
    return "PAPER_MORE_REQUIRED"


def latest_fear_exhaustion_v41_experiment(store_dir: Path = REPLAY_STORE_DIR) -> Path | None:
    experiments = sorted((store_dir / "experiments").glob("exp_*_fear_exhaustion_v41"), key=lambda path: path.name)
    return experiments[-1] if experiments else None


def _simulate_trade(frame: pd.DataFrame, entry_idx: int, market: str, signal_time: pd.Timestamp, candidate: dict, capital_krw: float, order_krw: float, config: FearExhaustionV41Config) -> dict | None:
    if entry_idx >= len(frame):
        return None
    entry_time = pd.Timestamp(frame.iloc[entry_idx]["time"])
    max_end = entry_time + pd.Timedelta(minutes=config.max_hold_minutes)
    outcome = frame[(frame["time"] >= entry_time) & (frame["time"] <= max_end)].copy()
    if outcome.empty:
        return None
    signal_price = float(outcome.iloc[0]["open"])
    stop = min(float(candidate["low"].get("low_2", signal_price * 0.994)), signal_price * 0.992)
    if config.exit_mode == "ma30":
        take_profit = max(signal_price * 1.004, float(candidate["ma"].get("ma30", signal_price * 1.004)))
    elif config.exit_mode == "fixed_rr":
        take_profit = signal_price + (signal_price - stop) * 1.2
    else:
        take_profit = max(signal_price * 1.004, float(candidate["bollinger"].get("middle_band", signal_price * 1.004)))
    fill = simulate_long_trade(outcome, signal_price, stop, take_profit, fee_pct=0.0, slippage_pct=0.0)
    pnl = calc_trade_pnl(capital_krw, order_krw, fill.pnl_pct, fee_pct=0.0, slippage_pct=0.0)
    return {
        "date_kst": signal_time.date().isoformat(),
        "market": market,
        "timeframe": config.timeframe,
        "signal_time_kst": signal_time.isoformat(),
        "entry_time_kst": entry_time.isoformat(),
        "exit_reason": fill.exit_reason,
        "entry_price": fill.entry_price,
        "exit_price": fill.exit_price,
        "hold_minutes": (pd.Timestamp(outcome.iloc[-1]["time"]) - entry_time).total_seconds() / 60,
        "v41_score": candidate["v41_score"],
        "skeptic_decision": candidate["skeptic_decision"],
        "would_block": candidate["would_block"],
        "blocking_applied": candidate["blocking_applied"],
        "entered": True,
        **pnl,
    }


def _flatten_candidate(candidate: dict) -> dict:
    return {
        "date_kst": candidate.get("date_kst"),
        "signal_time_kst": candidate.get("signal_time_kst"),
        "market": candidate["market"],
        "timeframe": candidate.get("timeframe"),
        "v41_score": candidate["v41_score"],
        "drop_pct": candidate["drop"]["drop_pct"],
        "drop_speed_score": candidate["drop"]["drop_speed_score"],
        "low_pattern": candidate["low"]["pattern"],
        "low_structure_score": candidate["low"]["low_structure_score"],
        "cooling_type": candidate["cooling"]["cooling_type"],
        "cooling_score": candidate["cooling"]["cooling_score"],
        "reentry_strength": candidate["bollinger"]["reentry_strength"],
        "support_sources": "|".join(candidate["support"]["support_sources"]),
        "support_context_score": candidate["support"]["support_context_score"],
        "target_space_pct": candidate["support"]["target_space_pct"],
        "skeptic_decision": candidate["skeptic_decision"],
        "skeptic_score": candidate["skeptic"]["skeptic_score"],
        "reject_reasons": "|".join(candidate["skeptic"]["reject_reasons"]),
        "warnings": "|".join(candidate["skeptic"]["warnings"]),
        "would_block": candidate["would_block"],
        "blocking_applied": candidate["blocking_applied"],
    }


def _empty_funnel(timeframe: str) -> dict:
    return {
        "timeframe": timeframe,
        "total_bars": 0,
        "drop_event_count": 0,
        "low_retest_or_lower_low_count": 0,
        "fear_cooling_count": 0,
        "bollinger_reentry_count": 0,
        "min_support_context_count": 0,
        "v41_score_pass_count": 0,
        "skeptic_pass_count": 0,
        "skeptic_warn_count": 0,
        "skeptic_reject_count": 0,
        "final_entry_count": 0,
    }


def _update_funnel(funnel: dict, candidate: dict) -> None:
    if candidate["has_drop_event"]:
        funnel["drop_event_count"] += 1
    if candidate["has_drop_event"] and candidate["has_low_structure"]:
        funnel["low_retest_or_lower_low_count"] += 1
    if candidate["has_drop_event"] and candidate["has_low_structure"] and candidate["has_fear_cooling"]:
        funnel["fear_cooling_count"] += 1
    if candidate["has_drop_event"] and candidate["has_low_structure"] and candidate["has_fear_cooling"] and candidate["reentered_lower_band"]:
        funnel["bollinger_reentry_count"] += 1
    if candidate["has_drop_event"] and candidate["has_low_structure"] and candidate["has_fear_cooling"] and candidate["reentered_lower_band"] and candidate["has_min_support"]:
        funnel["min_support_context_count"] += 1
    if candidate["has_drop_event"] and candidate["has_low_structure"] and candidate["has_fear_cooling"] and candidate["reentered_lower_band"] and candidate["has_min_support"] and candidate["score_pass"]:
        funnel["v41_score_pass_count"] += 1
        decision = candidate["skeptic_decision"]
        if decision == "PASS":
            funnel["skeptic_pass_count"] += 1
        elif decision == "WARN":
            funnel["skeptic_warn_count"] += 1
        else:
            funnel["skeptic_reject_count"] += 1
