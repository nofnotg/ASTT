from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from execution.risk_gate_v5 import evaluate_risk_gate_v5
from features.body_zone import body_zone_summary
from features.ichimoku_context import compute_ichimoku_context
from features.market_regime_filter import evaluate_market_regime
from features.mtf_score import compute_v5_score
from features.mtf_trend import compute_daily_structure, compute_h4_flow, compute_weekly_bias
from features.rs_flip import detect_rs_flip
from features.structure_reversal import classify_structure_reversal
from features.trendline_reclaim import detect_trendline_bounce, detect_trendline_break_reclaim
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fear_divergence_v4 import _load_timeframe_frame
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.research.small_seed_metrics import aggregate_small_seed_daily, aggregate_small_seed_monthly, aggregate_small_seed_weekly, calc_trade_pnl, summarize_trades


@dataclass(frozen=True)
class StructureReversalV5Config:
    weekly_min_score: float = 50.0
    daily_min_score: float = 60.0
    h4_min_score: float = 55.0
    v5_min_score: float = 75.0
    risk_reward_min: float = 1.2
    use_ichimoku: bool = False
    mode: str = "small_seed_daily"
    exit_mode: str = "fixed_rr"
    max_daily_entries: int = 1
    max_hold_minutes: int = 120
    strategy_types: tuple[str, ...] = ("TREND_CONTINUATION_PULLBACK", "FAILED_BREAKDOWN_RECLAIM", "BOTTOM_REVERSAL")


def run_structure_reversal_v5(
    start_date: date,
    end_date: date,
    markets: list[str],
    top_markets: int = 50,
    capital_krw: float = 500000,
    order_krw: float = 10000,
    mode: str = "small_seed_daily",
    max_daily_entries: int = 1,
    use_ichimoku: bool = False,
    strategy_types: list[str] | None = None,
    config: StructureReversalV5Config | None = None,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    config = config or StructureReversalV5Config(mode=mode, max_daily_entries=max_daily_entries, use_ichimoku=use_ichimoku, strategy_types=tuple(strategy_types or StructureReversalV5Config().strategy_types))
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_structure_reversal_v5")
    exp_dir = store_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    candidates, trades = scan_structure_reversal_v5(start_date, end_date, markets[:top_markets], capital_krw, order_krw, config, store_dir)
    daily = aggregate_small_seed_daily(trades.to_dict("records"), capital_krw)
    weekly = aggregate_small_seed_weekly(daily, capital_krw)
    monthly = aggregate_small_seed_monthly(daily, capital_krw)
    metrics = {
        **summarize_trades(trades.to_dict("records"), capital_krw),
        "capital_krw": capital_krw,
        "order_krw": order_krw,
        "candidate_count": int(len(candidates)),
        "mode": config.mode,
        "use_ichimoku": config.use_ichimoku,
        "risk_gate_active": True,
        "strategy_type_performance": _group_summary(trades, "strategy_type", capital_krw),
        "ichimoku_enabled_performance": _group_summary(trades, "use_ichimoku", capital_krw),
        "live_readiness": "LIVE_NOT_ALLOWED",
    }
    metrics["live_readiness"] = live_readiness_v5(metrics)
    (exp_dir / "config.json").write_text(json.dumps({"experiment_id": experiment_id, "mode": "STRUCTURE_REVERSAL_V5", "start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "markets": markets[:top_markets], **asdict(config)}, ensure_ascii=False, indent=2), encoding="utf-8")
    candidates.to_parquet(exp_dir / "candidates.parquet", index=False)
    trades.to_parquet(exp_dir / "paper_trades.parquet", index=False)
    daily.to_parquet(exp_dir / "daily_account.parquet", index=False)
    weekly.to_parquet(exp_dir / "weekly_account.parquet", index=False)
    monthly.to_parquet(exp_dir / "monthly_account.parquet", index=False)
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def scan_structure_reversal_v5(
    start_date: date,
    end_date: date,
    markets: list[str],
    capital_krw: float,
    order_krw: float,
    config: StructureReversalV5Config,
    store_dir: Path = REPLAY_STORE_DIR,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidates: list[dict[str, Any]] = []
    trades: list[dict[str, Any]] = []
    btc = _load_base_frame(store_dir, "KRW-BTC")
    for market in markets:
        base = _load_base_frame(store_dir, market)
        if base.empty:
            continue
        base = base[(base["time"] >= pd.Timestamp(start_date) - pd.Timedelta(days=90)) & (base["time"] <= pd.Timestamp(end_date) + pd.Timedelta(days=2))]
        if len(base) < 240:
            continue
        tf = _timeframes(base)
        signal_frame = tf["5m"]
        in_period = (signal_frame["time"] >= pd.Timestamp(start_date)) & (signal_frame["time"] <= pd.Timestamp(end_date) + pd.Timedelta(days=1))
        signal_indices = _trigger_indices(signal_frame[in_period])
        for idx in signal_indices:
            global_idx = int(idx)
            now = pd.Timestamp(signal_frame.iloc[global_idx]["time"])
            context = _context_until(tf, btc, now, market, config)
            candidate = evaluate_structure_reversal_candidate(context, market, now, config)
            if not candidate["is_candidate"]:
                continue
            candidates.append(_flatten_candidate(candidate))
            if candidate["risk_gate"]["risk_decision"] == "REJECT":
                continue
            trade = _simulate_trade(signal_frame, global_idx + 1, candidate, capital_krw, order_krw, config)
            if trade:
                trades.append(trade)
    candidate_frame = pd.DataFrame(candidates)
    trade_frame = pd.DataFrame(trades)
    if not trade_frame.empty:
        if config.mode == "weekly_sniper":
            trade_frame["week"] = pd.to_datetime(trade_frame["date_kst"]).dt.to_period("W-SUN").astype(str)
            trade_frame = trade_frame.sort_values(["week", "v5_score"], ascending=[True, False]).groupby("week", as_index=False).head(2).drop(columns=["week"])
        else:
            trade_frame = trade_frame.sort_values(["date_kst", "v5_score"], ascending=[True, False]).groupby("date_kst", as_index=False).head(config.max_daily_entries)
    return candidate_frame, trade_frame


def evaluate_structure_reversal_candidate(context: dict, market: str, now: pd.Timestamp, config: StructureReversalV5Config) -> dict:
    weekly = compute_weekly_bias(context["weekly"], context["daily"])
    daily = compute_daily_structure(context["daily"])
    h4 = compute_h4_flow(context["h4"])
    body = body_zone_summary(context["m15"], float(context["m15"].iloc[-1]["close"]) if not context["m15"].empty else 0.0)
    rs = detect_rs_flip(context["m15"], body.get("support_zone", [0.0, 0.0]))
    trend_break = detect_trendline_break_reclaim(context["h1"])
    trend_bounce = detect_trendline_bounce(context["m15"])
    trend = trend_break if trend_break["trendline_score"] >= trend_bounce["trendline_score"] else trend_bounce
    structure = classify_structure_reversal({"weekly": weekly, "daily": daily, "h4": h4, "rs_flip": rs, "trendline": trend, "body_zone": body})
    ichimoku = compute_ichimoku_context(context["daily"]) if config.use_ichimoku else {"ichimoku_score": 50.0, "long_allowed": True, "cloud_state": "DISABLED"}
    setup_score = max(rs["rs_flip_score"], trend["trendline_score"], body["body_zone_score"])
    trigger = _trigger_score(context["m5"], context["m1"])
    risk_reward = _risk_reward(context["m5"], body)
    score = compute_v5_score(
        {
            "weekly_bias_score": weekly["weekly_bias_score"],
            "daily_structure_score": daily["daily_structure_score"],
            "h4_flow_score": h4["h4_flow_score"],
            "structure_quality_score": structure["structure_quality_score"],
            "setup_score": setup_score,
            "trigger_score": trigger["trigger_score"],
            "risk_reward": risk_reward,
            "reasons": weekly.get("reasons", []) + daily.get("reasons", []) + h4.get("reasons", []),
        }
    )
    regime = evaluate_market_regime(context.get("btc_m5"), [])
    risk_gate = evaluate_risk_gate_v5(
        {
            "regime": regime,
            "risk_reward": risk_reward,
            "target_space_pct": body["target_space_pct"],
            "distance_to_resistance_pct": body["target_space_pct"],
            "data_quality": "GOOD",
        },
        minimum_rr=config.risk_reward_min,
    )
    is_candidate = (
        weekly["weekly_bias_score"] >= config.weekly_min_score
        and daily["daily_structure_score"] >= config.daily_min_score
        and h4["h4_flow_score"] >= config.h4_min_score
        and score["v5_score"] >= config.v5_min_score
        and structure["strategy_type"] in config.strategy_types
        and ichimoku.get("long_allowed", True)
    )
    return {
        "date_kst": now.date().isoformat(),
        "signal_time_kst": now.isoformat(),
        "market": market,
        "is_candidate": bool(is_candidate),
        "strategy_type": structure["strategy_type"],
        "weekly": weekly,
        "daily": daily,
        "h4": h4,
        "body": body,
        "rs_flip": rs,
        "trendline": trend,
        "ichimoku": ichimoku,
        "regime": regime,
        "risk_gate": risk_gate,
        "v5": score,
        "risk_reward": risk_reward,
        "target_space_pct": body["target_space_pct"],
        "trigger_score": trigger["trigger_score"],
        "setup_score": setup_score,
        "use_ichimoku": config.use_ichimoku,
    }


def live_readiness_v5(metrics: dict) -> str:
    if metrics.get("entry_count", 0) < 30:
        return "LIVE_NOT_ALLOWED"
    if not metrics.get("risk_gate_active", False):
        return "LIVE_NOT_ALLOWED"
    if metrics.get("account_return_pct", 0.0) <= 0 or metrics.get("profit_factor", 0.0) < 0.9 or metrics.get("consecutive_loss_max", 0) > 4:
        return "LIVE_NOT_ALLOWED"
    if metrics.get("profit_factor", 0.0) >= 1.1 and metrics.get("max_drawdown_pct", 0.0) >= -8.0 and metrics.get("consecutive_loss_max", 0) <= 3:
        return "MICRO_LIVE_READY"
    return "PAPER_MORE_REQUIRED"


def latest_structure_reversal_v5_experiment(store_dir: Path = REPLAY_STORE_DIR, mode: str | None = None) -> Path | None:
    experiments = sorted((store_dir / "experiments").glob("exp_*_structure_reversal_v5"), key=lambda path: path.name)
    if not mode:
        return experiments[-1] if experiments else None
    for experiment in reversed(experiments):
        metrics_path = experiment / "metrics.json"
        if metrics_path.exists():
            try:
                metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if metrics.get("mode") == mode:
                return experiment
    return None


def _load_base_frame(store_dir: Path, market: str) -> pd.DataFrame:
    path = store_dir / "normalized" / "candles_1m" / f"{market}.parquet"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_parquet(path)
    frame["time"] = pd.to_datetime(frame.get("candle_time_kst", frame.get("time")))
    return frame.sort_values("time")[["time", "open", "high", "low", "close", "volume", "trade_price"]].copy()


def _timeframes(base: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"1m": base, "5m": _resample(base, "5min"), "15m": _resample(base, "15min"), "1h": _resample(base, "60min"), "4h": _resample(base, "240min"), "1d": _resample(base, "1D"), "1w": _resample(base, "1W")}


def _resample(frame: pd.DataFrame, rule: str) -> pd.DataFrame:
    return frame.set_index("time").resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "trade_price": "sum"}).dropna().reset_index()


def _trigger_indices(frame: pd.DataFrame) -> list[int]:
    if frame.empty:
        return []
    data = frame.copy()
    volume = data["volume"].astype(float)
    close = data["close"].astype(float)
    ma = close.rolling(20, min_periods=5).mean()
    mask = (close > ma) & (volume > volume.rolling(20, min_periods=5).mean() * 1.05)
    local_positions = data.index[mask.fillna(False)].tolist()
    return local_positions[:800]


def _context_until(tf: dict[str, pd.DataFrame], btc: pd.DataFrame, now: pd.Timestamp, market: str, config: StructureReversalV5Config) -> dict:
    return {
        "weekly": tf["1w"][tf["1w"]["time"] <= now].tail(40),
        "daily": tf["1d"][tf["1d"]["time"] <= now].tail(120),
        "h4": tf["4h"][tf["4h"]["time"] <= now].tail(120),
        "h1": tf["1h"][tf["1h"]["time"] <= now].tail(120),
        "m15": tf["15m"][tf["15m"]["time"] <= now].tail(120),
        "m5": tf["5m"][tf["5m"]["time"] <= now].tail(80),
        "m1": tf["1m"][tf["1m"]["time"] <= now].tail(80),
        "btc_m5": _resample(btc[btc["time"] <= now].tail(300), "5min") if not btc.empty else pd.DataFrame(),
    }


def _trigger_score(m5: pd.DataFrame, m1: pd.DataFrame) -> dict:
    if m5.empty:
        return {"trigger_score": 0.0}
    close = m5["close"].astype(float)
    volume = m5["volume"].astype(float)
    score = 35.0
    if float(close.iloc[-1]) >= float(close.rolling(20, min_periods=5).mean().iloc[-1]):
        score += 25
    if float(volume.tail(2).mean()) >= float(volume.tail(20).mean()) * 1.05:
        score += 25
    if not m1.empty and float(m1.iloc[-1]["close"]) >= float(m1["close"].tail(10).mean()):
        score += 15
    return {"trigger_score": float(max(0.0, min(100.0, score)))}


def _risk_reward(m5: pd.DataFrame, body: dict) -> float:
    if m5.empty:
        return 0.0
    current = float(m5.iloc[-1]["close"])
    recent_low = float(m5["low"].tail(12).min())
    stop_pct = max(0.35, (current - recent_low) / current * 100 if current else 0.8)
    target = max(0.6, min(2.0, float(body.get("target_space_pct", 0.8))))
    return target / stop_pct if stop_pct else 0.0


def _simulate_trade(signal_frame: pd.DataFrame, entry_idx: int, candidate: dict, capital_krw: float, order_krw: float, config: StructureReversalV5Config) -> dict | None:
    if entry_idx >= len(signal_frame):
        return None
    entry_time = pd.Timestamp(signal_frame.iloc[entry_idx]["time"])
    max_end = entry_time + pd.Timedelta(minutes=config.max_hold_minutes if config.mode != "weekly_sniper" else 2880)
    outcome = signal_frame[(signal_frame["time"] >= entry_time) & (signal_frame["time"] <= max_end)].copy()
    if outcome.empty:
        return None
    entry = float(outcome.iloc[0]["open"])
    stop = entry * (1 - min(1.5, max(0.4, 1 / max(0.1, candidate["risk_reward"]))) / 100)
    if config.exit_mode == "time_stop":
        take = entry * 1.006
    elif config.exit_mode == "body_resistance":
        take = entry * (1 + max(0.6, min(2.0, candidate["target_space_pct"])) / 100)
    else:
        take = entry + (entry - stop) * max(config.risk_reward_min, 1.2)
    fill = simulate_long_trade(outcome, entry, stop, take, fee_pct=0.0, slippage_pct=0.0)
    pnl = calc_trade_pnl(capital_krw, order_krw, fill.pnl_pct, fee_pct=0.0, slippage_pct=0.0)
    return {
        "date_kst": candidate["date_kst"],
        "market": candidate["market"],
        "signal_time_kst": candidate["signal_time_kst"],
        "entry_time_kst": entry_time.isoformat(),
        "exit_reason": fill.exit_reason,
        "entry_price": fill.entry_price,
        "exit_price": fill.exit_price,
        "hold_minutes": (pd.Timestamp(outcome.iloc[-1]["time"]) - entry_time).total_seconds() / 60,
        "strategy_type": candidate["strategy_type"],
        "v5_score": candidate["v5"]["v5_score"],
        "weekly_bias_score": candidate["weekly"]["weekly_bias_score"],
        "daily_structure_score": candidate["daily"]["daily_structure_score"],
        "h4_flow_score": candidate["h4"]["h4_flow_score"],
        "risk_reward": candidate["risk_reward"],
        "use_ichimoku": candidate["use_ichimoku"],
        "risk_decision": candidate["risk_gate"]["risk_decision"],
        "entered": True,
        **pnl,
    }


def _flatten_candidate(candidate: dict) -> dict:
    return {
        "date_kst": candidate["date_kst"],
        "signal_time_kst": candidate["signal_time_kst"],
        "market": candidate["market"],
        "strategy_type": candidate["strategy_type"],
        "weekly_bias_score": candidate["weekly"]["weekly_bias_score"],
        "daily_structure_score": candidate["daily"]["daily_structure_score"],
        "h4_flow_score": candidate["h4"]["h4_flow_score"],
        "setup_score": candidate["setup_score"],
        "trigger_score": candidate["trigger_score"],
        "risk_reward": candidate["risk_reward"],
        "target_space_pct": candidate["target_space_pct"],
        "v5_score": candidate["v5"]["v5_score"],
        "grade": candidate["v5"]["grade"],
        "risk_decision": candidate["risk_gate"]["risk_decision"],
        "veto_reasons": "|".join(candidate["risk_gate"]["veto_reasons"]),
        "use_ichimoku": candidate["use_ichimoku"],
    }


def _group_summary(frame: pd.DataFrame, column: str, capital_krw: float) -> list[dict]:
    if frame.empty or column not in frame:
        return []
    rows = []
    for value, group in frame.groupby(column):
        rows.append({"key": str(value), **summarize_trades(group.to_dict("records"), capital_krw)})
    return rows
