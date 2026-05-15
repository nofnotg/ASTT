from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import TradingMode, get_settings
from decision.debate_engine import decide
from features.regime import calculate_regime
from personas import costa, iris, maggie, mr_k, rezo
from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.data_quality import evaluate_candles
from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade


@dataclass(frozen=True)
class EntryGateConfig:
    min_final_score: float = 82.0
    min_rezo_score: float = 80.0
    min_maggie_score: float = 80.0
    min_confidence: float = 70.0
    min_weekly_trend_score: float = 45.0
    min_daily_trend_score: float = 45.0
    min_morning_liquidity_score: float = 45.0


@dataclass(frozen=True)
class EntryGateDecision:
    decision: str
    confidence: float
    reason: str
    threshold_profile: str = "v2_default"


def _maggie_score(persona_scores: dict[str, float]) -> float:
    return float(persona_scores.get("Maggie", persona_scores.get("\ub9e4\uae30", 0.0)))


def _dt(day: date, hhmm: str) -> datetime:
    hour, minute = [int(part) for part in hhmm.split(":")]
    return datetime.combine(day, time(hour, minute))


def _score_range(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.0
    return max(0.0, min(100.0, (value - low) / (high - low) * 100.0))


def _pct_change(start: float, end: float) -> float:
    return (end - start) / start * 100 if start else 0.0


def _slice(frame: pd.DataFrame, start: datetime, end: datetime) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame.copy()
    data["time"] = pd.to_datetime(data["time"])
    return data[(data["time"] >= pd.Timestamp(start)) & (data["time"] <= pd.Timestamp(end))]


def build_v2_features(provider: ReplayDataProvider, market: str, day: date, decision_time: datetime) -> dict[str, float]:
    candles = provider.get_candles(market, "1m", 2200, decision_time)
    if candles.empty:
        return {
            "weekly_trend_score": 0.0,
            "daily_trend_score": 0.0,
            "h4_trend_score": 0.0,
            "morning_liquidity_score": 0.0,
            "preopen_volume_score": 0.0,
            "btc_context_score": 50.0,
        }
    today_start = _dt(day, "00:00")
    decision_start = decision_time
    prev_start = today_start - timedelta(days=1)
    h4_start = decision_time - timedelta(hours=4)
    morning_start = _dt(day, "07:00")
    preopen_start = _dt(day, "08:30")
    preopen_focus = _dt(day, "08:50")

    prev = _slice(candles, prev_start, today_start - timedelta(minutes=1))
    today = _slice(candles, today_start, decision_start)
    h4 = _slice(candles, h4_start, decision_start)
    morning = _slice(candles, morning_start, decision_start)
    preopen = _slice(candles, preopen_start, decision_start)
    focus = _slice(candles, preopen_focus, decision_start)

    long_frame = candles.tail(min(len(candles), 7 * 24 * 60))
    weekly_return = _pct_change(float(long_frame.iloc[0]["open"]), float(long_frame.iloc[-1]["close"])) if len(long_frame) > 1 else 0.0
    weekly_trend = _score_range(weekly_return, -8.0, 8.0)

    daily_return = _pct_change(float(today.iloc[0]["open"]), float(today.iloc[-1]["close"])) if len(today) > 1 else 0.0
    daily_value = float(today["trade_price"].sum()) if not today.empty else 0.0
    prev_value = float(prev["trade_price"].sum()) if not prev.empty else daily_value
    daily_liquidity_ratio = daily_value / prev_value if prev_value else 0.0
    daily_trend = (_score_range(daily_return, -4.0, 4.0) * 0.65) + (_score_range(daily_liquidity_ratio, 0.05, 0.8) * 0.35)

    h4_return = _pct_change(float(h4.iloc[0]["open"]), float(h4.iloc[-1]["close"])) if len(h4) > 1 else 0.0
    h4_trend = _score_range(h4_return, -2.5, 2.5)

    baseline = float(today[today["time"] < pd.Timestamp(morning_start)]["trade_price"].mean()) if not today.empty else 0.0
    morning_avg = float(morning["trade_price"].mean()) if not morning.empty else 0.0
    morning_liquidity = _score_range(morning_avg / baseline if baseline else 0.0, 0.7, 3.0)

    pre_avg = float(preopen["trade_price"].mean()) if not preopen.empty else 0.0
    focus_avg = float(focus["trade_price"].mean()) if not focus.empty else 0.0
    pre_return = _pct_change(float(focus.iloc[0]["open"]), float(focus.iloc[-1]["close"])) if len(focus) > 1 else 0.0
    preopen_volume = (_score_range(focus_avg / pre_avg if pre_avg else 0.0, 0.8, 3.0) * 0.7) + (_score_range(pre_return, -1.0, 1.5) * 0.3)

    btc_context = 50.0
    if market != "KRW-BTC":
        btc = provider.get_candles("KRW-BTC", "1m", 300, decision_time)
        btc_today = _slice(btc, today_start, decision_start)
        if len(btc_today) > 1:
            btc_context = _score_range(_pct_change(float(btc_today.iloc[0]["open"]), float(btc_today.iloc[-1]["close"])), -2.0, 2.0)

    return {
        "weekly_trend_score": round(weekly_trend, 4),
        "daily_trend_score": round(daily_trend, 4),
        "h4_trend_score": round(h4_trend, 4),
        "morning_liquidity_score": round(morning_liquidity, 4),
        "preopen_volume_score": round(preopen_volume, 4),
        "btc_context_score": round(btc_context, 4),
    }


def entry_gate(
    final_score: float,
    persona_scores: dict[str, float],
    persona_decisions: dict[str, str],
    data_quality: str,
    features: dict[str, float],
    config: EntryGateConfig | None = None,
) -> EntryGateDecision:
    config = config or EntryGateConfig()
    reasons = []
    if data_quality == "LOW_QUALITY":
        return EntryGateDecision("REJECT", 0.0, "data quality low")
    if persona_decisions.get("Iris") == "VETO":
        return EntryGateDecision("REJECT", 0.0, "Iris veto")
    if final_score < config.min_final_score:
        reasons.append(f"final_score {final_score:.1f} < {config.min_final_score:.1f}")
    if persona_scores.get("Rezo", 0.0) < config.min_rezo_score:
        reasons.append(f"Rezo {persona_scores.get('Rezo', 0.0):.1f} < {config.min_rezo_score:.1f}")
    maggie_score = _maggie_score(persona_scores)
    if maggie_score < config.min_maggie_score:
        reasons.append(f"Maggie {maggie_score:.1f} < {config.min_maggie_score:.1f}")
    for key, minimum in [
        ("weekly_trend_score", config.min_weekly_trend_score),
        ("daily_trend_score", config.min_daily_trend_score),
        ("morning_liquidity_score", config.min_morning_liquidity_score),
    ]:
        if features.get(key, 0.0) < minimum:
            reasons.append(f"{key} {features.get(key, 0.0):.1f} < {minimum:.1f}")

    confidence = (
        final_score * 0.30
        + persona_scores.get("Rezo", 0.0) * 0.20
        + maggie_score * 0.18
        + features.get("weekly_trend_score", 0.0) * 0.08
        + features.get("daily_trend_score", 0.0) * 0.08
        + features.get("h4_trend_score", 0.0) * 0.06
        + features.get("morning_liquidity_score", 0.0) * 0.05
        + features.get("preopen_volume_score", 0.0) * 0.05
    )
    confidence = round(max(0.0, min(100.0, confidence)), 4)
    if confidence < config.min_confidence:
        reasons.append(f"confidence {confidence:.1f} < {config.min_confidence:.1f}")
    if reasons:
        return EntryGateDecision("HOLD", confidence, "; ".join(reasons))
    return EntryGateDecision("ENTER", confidence, "all v2 thresholds passed")


def run_study_v2(
    start_date: date,
    end_date: date,
    markets: list[str],
    candidate_limit: int = 10,
    max_daily_entries: int = 1,
    capital_krw: float = 500000,
    load_first: bool = True,
    store_dir: Path = REPLAY_STORE_DIR,
) -> Path:
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_v2")
    exp_dir = store_dir / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    config_payload = {
        "experiment_id": experiment_id,
        "mode": "PAPER_REPLAY_V2",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "candidate_limit": candidate_limit,
        "max_daily_entries": max_daily_entries,
        "capital_krw": capital_krw,
        "threshold_profile": "v2_default",
    }
    (exp_dir / "config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    loader = HistoricalLoader(store_dir=store_dir)
    clock = ReplayClock(_dt(start_date, "08:50"))
    provider = ReplayDataProvider(clock, store_dir=store_dir)
    settings = get_settings(TRADING_MODE=TradingMode.PAPER, UPBIT_ACCESS_KEY="", UPBIT_SECRET_KEY="")
    all_sessions: list[pd.DataFrame] = []
    all_personas: list[pd.DataFrame] = []
    all_decisions: list[pd.DataFrame] = []
    all_trades: list[pd.DataFrame] = []
    all_universe: list[pd.DataFrame] = []
    progress = exp_dir / "progress.jsonl"

    day = start_date
    while day <= end_date:
        scoped_markets = list(dict.fromkeys(["KRW-BTC", *markets]))
        if load_first:
            for market in scoped_markets:
                loader.load_candles(market, "1m", _dt(day, "00:00") - timedelta(days=2), _dt(day, "10:00"))
        result = run_day_v2(day, markets, provider, clock, candidate_limit, max_daily_entries, capital_krw, experiment_id, settings)
        for key, bucket in [
            ("session_results", all_sessions),
            ("persona_scores", all_personas),
            ("decisions", all_decisions),
            ("paper_trades", all_trades),
            ("universe_stages", all_universe),
        ]:
            bucket.append(result[key])
        summary = {"date": day.isoformat(), "candidates": int(len(result["decisions"])), "entries": int(len(result["paper_trades"]))}
        with progress.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, ensure_ascii=False) + "\n")
        day += timedelta(days=1)

    written = {}
    for filename, frames in [
        ("session_results", all_sessions),
        ("persona_scores", all_personas),
        ("decisions", all_decisions),
        ("paper_trades", all_trades),
        ("universe_stages", all_universe),
    ]:
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        frame.to_parquet(exp_dir / f"{filename}.parquet", index=False)
        written[filename] = int(len(frame))
    (exp_dir / "metrics.json").write_text(json.dumps(written, ensure_ascii=False, indent=2), encoding="utf-8")
    return exp_dir


def run_day_v2(
    day: date,
    markets: list[str],
    provider: ReplayDataProvider,
    clock: ReplayClock,
    candidate_limit: int,
    max_daily_entries: int,
    capital_krw: float,
    experiment_id: str,
    settings: Any | None = None,
) -> dict[str, pd.DataFrame]:
    settings = settings or get_settings(TRADING_MODE=TradingMode.PAPER, UPBIT_ACCESS_KEY="", UPBIT_SECRET_KEY="")
    decision_time = _dt(day, "08:59")
    entry_time = _dt(day, "09:00")
    trade_end = _dt(day, "10:00")
    clock.set(decision_time)

    sessions = []
    personas_rows = []
    decision_rows = []
    trade_rows = []
    universe_rows = []
    raw_candidates = []

    for market in markets:
        candles = provider.get_candles(market, "1m", 2200, decision_time)
        if candles.empty:
            universe_rows.append(_stage_row(day, market, "missing_data", False, 0.0))
            continue
        quality = evaluate_candles(candles.rename(columns={"time": "candle_time_kst"}))
        features = build_v2_features(provider, market, day, decision_time)
        universe_score = _universe_score(features)
        for stage, key, minimum in [
            ("weekly_trend", "weekly_trend_score", 35.0),
            ("daily_trend", "daily_trend_score", 35.0),
            ("h4_trend", "h4_trend_score", 30.0),
            ("morning_liquidity", "morning_liquidity_score", 30.0),
            ("preopen_volume", "preopen_volume_score", 0.0),
        ]:
            universe_rows.append(_stage_row(day, market, stage, features.get(key, 0.0) >= minimum, features.get(key, 0.0), features))
        passed = _stage_pass(features)
        universe_rows.append(_stage_row(day, market, "candidate_pool", passed, universe_score, features))
        if passed:
            raw_candidates.append((market, universe_score, quality, features, candles))

    raw_candidates = sorted(raw_candidates, key=lambda item: item[1], reverse=True)[: max(candidate_limit, max_daily_entries)]
    if not raw_candidates:
        session_id = f"{experiment_id}_{day.isoformat()}_NO_ENTRY"
        sessions.append(
            {
                "session_id": session_id,
                "date_kst": day.isoformat(),
                "market": "",
                "candidate": False,
                "data_quality": "NO_CANDIDATE",
                "universe_score": 0.0,
            }
        )
        decision_rows.append(
            {
                "session_id": session_id,
                "date_kst": day.isoformat(),
                "market": "",
                "decision_time_kst": decision_time.isoformat(),
                "entry_time_kst": entry_time.isoformat(),
                "target_window_end_time_kst": _dt(day, "09:30").isoformat(),
                "trade_end_time_kst": trade_end.isoformat(),
                "strategy_label": "v2_entry_gate_0900",
                "day_type": "weekend" if day.weekday() >= 5 else "weekday",
                "final_score": 0.0,
                "final_decision": "HOLD",
                "entry_gate_decision": "HOLD",
                "entry_gate_confidence": 0.0,
                "entry_gate_reason": "no market passed multi-timeframe universe filter",
                "threshold_profile": "v2_default",
                "entered_by_v2": False,
                "universe_stage": "no_candidate",
                "no_entry_reason": "no market passed multi-timeframe universe filter",
                "weekly_trend_score": 0.0,
                "daily_trend_score": 0.0,
                "h4_trend_score": 0.0,
                "morning_liquidity_score": 0.0,
                "preopen_volume_score": 0.0,
                "btc_context_score": 50.0,
            }
        )
        return {
            "session_results": pd.DataFrame(sessions),
            "persona_scores": pd.DataFrame(personas_rows),
            "decisions": pd.DataFrame(decision_rows),
            "paper_trades": pd.DataFrame(trade_rows),
            "universe_stages": pd.DataFrame(universe_rows),
        }

    entered = 0
    for market, universe_score, quality, features, candles in raw_candidates:
        trades_proxy = provider.get_trade_proxy(market, decision_time)
        regime = calculate_regime(candles)
        price = float(candles["close"].iloc[-1]) if not candles.empty else 0.0
        context = {
            "market": market,
            "candles": candles,
            "trades": trades_proxy,
            "regime": regime,
            "price": price,
            "risk_reward": 1.8,
            "spread_pct": 0.1,
            "daily_loss_pct": 0.0,
            "open_positions": 0,
            "krw_amount": settings.min_order_krw,
            "btc_shock": features.get("btc_context_score", 50.0) < 30,
            "data_quality_warning": "LOW_QUALITY" if quality["quality"] == "LOW_QUALITY" else None,
        }
        results = [
            mr_k.analyze(context),
            maggie.analyze(context),
            rezo.analyze(context),
            costa.analyze(context, settings),
            iris.analyze(context, settings),
        ]
        final = decide(market, results, settings)
        score_map = {_display_persona(item.persona_name): float(item.score) for item in results}
        decision_map = {_display_persona(item.persona_name): item.decision for item in results}
        gate = entry_gate(final.final_score, score_map, decision_map, quality["quality"], features)
        if gate.decision == "ENTER" and entered >= max_daily_entries:
            gate = EntryGateDecision("HOLD", gate.confidence, "daily entry limit reached")

        session_id = f"{experiment_id}_{day.isoformat()}_{market}"
        sessions.append(
            {
                "session_id": session_id,
                "date_kst": day.isoformat(),
                "market": market,
                "candidate": True,
                "data_quality": quality["quality"],
                "universe_score": universe_score,
                **features,
            }
        )
        for item in results:
            personas_rows.append(
                {
                    "session_id": session_id,
                    "date_kst": day.isoformat(),
                    "market": market,
                    "persona": _display_persona(item.persona_name),
                    "score": item.score,
                    "decision": item.decision,
                    "veto": item.veto,
                    "veto_reason": item.veto_reason,
                    "reasons": item.reasons,
                    "warnings": item.warnings,
                }
            )
        decision_rows.append(
            {
                "session_id": session_id,
                "date_kst": day.isoformat(),
                "market": market,
                "decision_time_kst": decision_time.isoformat(),
                "entry_time_kst": entry_time.isoformat(),
                "target_window_end_time_kst": _dt(day, "09:30").isoformat(),
                "trade_end_time_kst": trade_end.isoformat(),
                "strategy_label": "v2_entry_gate_0900",
                "day_type": "weekend" if day.weekday() >= 5 else "weekday",
                "final_score": final.final_score,
                "final_decision": final.decision,
                "entry_gate_decision": gate.decision,
                "entry_gate_confidence": gate.confidence,
                "entry_gate_reason": gate.reason,
                "threshold_profile": gate.threshold_profile,
                "entered_by_v2": gate.decision == "ENTER",
                "universe_stage": "candidate_limit",
                "no_entry_reason": "" if gate.decision == "ENTER" else gate.reason,
                **features,
            }
        )
        if gate.decision == "ENTER":
            trade = _simulate_trade(provider, clock, day, market, session_id, final.final_score, gate, features)
            if trade:
                trade_rows.append(trade)
                entered += 1

    return {
        "session_results": pd.DataFrame(sessions),
        "persona_scores": pd.DataFrame(personas_rows),
        "decisions": pd.DataFrame(decision_rows),
        "paper_trades": pd.DataFrame(trade_rows),
        "universe_stages": pd.DataFrame(universe_rows),
    }


def _simulate_trade(provider: ReplayDataProvider, clock: ReplayClock, day: date, market: str, session_id: str, final_score: float, gate: EntryGateDecision, features: dict[str, float]) -> dict | None:
    entry_time = _dt(day, "09:00")
    trade_end = _dt(day, "10:00")
    clock.set(trade_end)
    outcome = provider.get_candles(market, "1s", 4500)
    fill_timeframe = "1s"
    if outcome.empty:
        outcome = provider.get_candles(market, "1m", 100)
        fill_timeframe = "1m"
    outcome = outcome[outcome["time"] >= pd.Timestamp(entry_time)]
    if outcome.empty:
        return None
    signal_price = float(outcome.iloc[0]["open"])
    fill = simulate_long_trade(outcome, signal_price, signal_price * 0.985, signal_price * 1.015)
    return {
        "session_id": session_id,
        "date_kst": day.isoformat(),
        "market": market,
        "decision_time_kst": _dt(day, "08:59").isoformat(),
        "entry_time_kst": entry_time.isoformat(),
        "target_window_end_time_kst": _dt(day, "09:30").isoformat(),
        "trade_end_time_kst": trade_end.isoformat(),
        "strategy_label": "v2_entry_gate_0900",
        "day_type": "weekend" if day.weekday() >= 5 else "weekday",
        "fill_timeframe": fill_timeframe,
        "entered_by_v2": True,
        "entry_gate_confidence": gate.confidence,
        "entry_gate_reason": gate.reason,
        "final_score": final_score,
        **features,
        **asdict(fill),
    }


def _universe_score(features: dict[str, float]) -> float:
    return round(
        features.get("weekly_trend_score", 0.0) * 0.18
        + features.get("daily_trend_score", 0.0) * 0.22
        + features.get("h4_trend_score", 0.0) * 0.18
        + features.get("morning_liquidity_score", 0.0) * 0.22
        + features.get("preopen_volume_score", 0.0) * 0.15
        + features.get("btc_context_score", 50.0) * 0.05,
        4,
    )


def _stage_pass(features: dict[str, float]) -> bool:
    return (
        features.get("weekly_trend_score", 0.0) >= 35.0
        and features.get("daily_trend_score", 0.0) >= 35.0
        and features.get("h4_trend_score", 0.0) >= 30.0
        and features.get("morning_liquidity_score", 0.0) >= 30.0
    )


def _stage_row(day: date, market: str, stage: str, passed: bool, score: float, features: dict[str, float] | None = None) -> dict[str, Any]:
    return {
        "date_kst": day.isoformat(),
        "market": market,
        "universe_stage": stage,
        "passed": passed,
        "universe_score": score,
        **(features or {}),
    }


def _display_persona(name: str) -> str:
    if name in {"Mr.K", "Rezo", "CostA", "Iris"}:
        return name
    return "Maggie"
