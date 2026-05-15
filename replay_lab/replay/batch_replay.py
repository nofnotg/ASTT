from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.historical_loader import HistoricalLoader
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.feedback.replay_report import write_replay_report
from replay_lab.paths import REPLAY_STORE_DIR
from replay_lab.replay.fill_replay import simulate_long_trade
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig
from replay_lab.research.experiment_registry import ExperimentRegistry


def run_batch_0900(
    days: int,
    markets: list[str],
    top_markets: int | None = None,
    end_date: date | None = None,
    scan_time: str = "08:50",
    pre_score_time: str = "08:59",
    decision_time: str = "08:59",
    entry_time: str = "09:00",
    target_window_end_time: str = "09:30",
    trade_end_time: str = "10:00",
    strategy_label: str = "0850_0900_scalp",
) -> Path:
    end_date = end_date or date.today()
    start_date = end_date - timedelta(days=days - 1)
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S")
    exp_dir = REPLAY_STORE_DIR / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / "config.json").write_text(
        json.dumps(
            {
                "experiment_id": experiment_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "markets": markets,
                "top_markets": top_markets,
                "scan_time": scan_time,
                "pre_score_time": pre_score_time,
                "decision_time": decision_time,
                "entry_time": entry_time,
                "target_window_end_time": target_window_end_time,
                "trade_end_time": trade_end_time,
                "strategy_label": strategy_label,
                "mode": "PAPER_REPLAY",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    all_results: dict[str, list[pd.DataFrame]] = {"session_results": [], "persona_scores": [], "decisions": [], "paper_trades": [], "feature_snapshots": []}
    clock = ReplayClock(datetime.combine(start_date, datetime.min.time()))
    provider = ReplayDataProvider(clock)
    runner = ReplayRunner0900(provider, clock)
    day = start_date
    while day <= end_date:
        config = ReplaySessionConfig(
            session_id=f"{experiment_id}_{day.isoformat()}",
            date_kst=day,
            markets=markets,
            scan_time=scan_time,
            pre_score_time=pre_score_time,
            decision_time=decision_time,
            entry_time=entry_time,
            target_window_end_time=target_window_end_time,
            trade_end_time=trade_end_time,
            strategy_label=strategy_label,
        )
        result = runner.run(config, top_market_limit=top_markets)
        for key, frame in result.items():
            all_results[key].append(frame)
        day += timedelta(days=1)
    written = {}
    for key, frames in all_results.items():
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        path = exp_dir / f"{key}.parquet"
        frame.to_parquet(path, index=False)
        written[key] = frame
    report_path = write_replay_report(exp_dir, experiment_id, written)
    ExperimentRegistry().upsert_completed(experiment_id, start_date.isoformat(), end_date.isoformat(), f"top{top_markets or len(markets)}", report_path, written)
    return exp_dir


def run_daily_study_0900(
    start_date: date,
    end_date: date,
    markets: list[str],
    top_markets: int | None = None,
    load_first: bool = True,
    use_seconds: bool = False,
    force_daily_entries: bool = False,
    force_daily_count: int = 1,
    scan_time: str = "08:50",
    pre_score_time: str = "08:59",
    decision_time: str = "08:59",
    entry_time: str = "09:00",
    target_window_end_time: str = "09:30",
    trade_end_time: str = "10:00",
    strategy_label: str = "0850_0900_scalp",
) -> Path:
    experiment_id = datetime.utcnow().strftime("exp_%Y%m%d_%H%M%S_daily")
    exp_dir = REPLAY_STORE_DIR / "experiments" / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    config_payload = {
        "experiment_id": experiment_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "markets": markets,
        "top_markets": top_markets,
        "load_first": load_first,
        "use_seconds": use_seconds,
        "force_daily_entries": force_daily_entries,
        "force_daily_count": force_daily_count,
        "scan_time": scan_time,
        "pre_score_time": pre_score_time,
        "decision_time": decision_time,
        "entry_time": entry_time,
        "target_window_end_time": target_window_end_time,
        "trade_end_time": trade_end_time,
        "strategy_label": strategy_label,
        "mode": "PAPER_REPLAY_DAILY_STUDY",
        "note": "Loads and replays one date at a time. ReplayClock still blocks future candles.",
    }
    (exp_dir / "config.json").write_text(json.dumps(config_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    all_results: dict[str, list[pd.DataFrame]] = {"session_results": [], "persona_scores": [], "decisions": [], "paper_trades": [], "feature_snapshots": []}
    progress_path = exp_dir / "progress.jsonl"
    loader = HistoricalLoader()
    clock = ReplayClock(datetime.combine(start_date, datetime.min.time()))
    provider = ReplayDataProvider(clock)
    runner = ReplayRunner0900(provider, clock)

    day = start_date
    while day <= end_date:
        if load_first:
            loader.load_batch_0900_windows(markets[: top_markets or len(markets)], day, day)
            if use_seconds:
                loader.load_batch_0900_seconds_windows(markets[: top_markets or len(markets)], day, day)
        config = ReplaySessionConfig(
            session_id=f"{experiment_id}_{day.isoformat()}",
            date_kst=day,
            markets=markets,
            scan_time=scan_time,
            pre_score_time=pre_score_time,
            decision_time=decision_time,
            entry_time=entry_time,
            target_window_end_time=target_window_end_time,
            trade_end_time=trade_end_time,
            strategy_label=strategy_label,
        )
        result = runner.run(config, top_market_limit=top_markets)
        if force_daily_entries:
            result = _ensure_forced_daily_entries(result, provider, clock, config, force_daily_count)
        daily_summary = {
            "date": day.isoformat(),
            "sessions": int(len(result["session_results"])),
            "decisions": int(len(result["decisions"])),
            "entries": int(len(result["paper_trades"])),
            "wins": int((result["paper_trades"].get("pnl_pct", pd.Series(dtype=float)) > 0).sum()) if not result["paper_trades"].empty else 0,
        }
        with progress_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(daily_summary, ensure_ascii=False) + "\n")
        for key, frame in result.items():
            all_results[key].append(frame)
        day += timedelta(days=1)

    written = {}
    for key, frames in all_results.items():
        frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        path = exp_dir / f"{key}.parquet"
        frame.to_parquet(path, index=False)
        written[key] = frame
    report_path = write_replay_report(exp_dir, experiment_id, written)
    ExperimentRegistry().upsert_completed(experiment_id, start_date.isoformat(), end_date.isoformat(), f"top{top_markets or len(markets)}_daily", report_path, written)
    return exp_dir


def _hhmm(day: date, value: str) -> datetime:
    hour, minute = [int(part) for part in value.split(":")]
    return datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)


def _ensure_forced_daily_entries(
    result: dict[str, pd.DataFrame],
    provider: ReplayDataProvider,
    clock: ReplayClock,
    config: ReplaySessionConfig,
    force_count: int,
) -> dict[str, pd.DataFrame]:
    decisions = result.get("decisions", pd.DataFrame()).copy()
    trades = result.get("paper_trades", pd.DataFrame()).copy()
    existing = set(trades.get("market", pd.Series(dtype=str)).astype(str).tolist()) if not trades.empty else set()
    needed = max(0, force_count - len(existing))
    if needed <= 0 or decisions.empty:
        return result
    candidates = decisions[~decisions["market"].astype(str).isin(existing)].copy()
    non_veto = candidates[candidates.get("vetoed", pd.Series(dtype=bool)) != True]
    if not non_veto.empty:
        candidates = non_veto
    candidates = candidates.sort_values(["final_score", "market"], ascending=[False, True]).head(needed)
    forced_rows = []
    for _, row in candidates.iterrows():
        forced = _simulate_forced_entry(row, provider, clock, config)
        if forced:
            forced_rows.append(forced)
            decisions.loc[decisions["market"] == row["market"], "forced_entry"] = True
            decisions.loc[decisions["market"] == row["market"], "force_entry_reason"] = "daily_best_candidate"
    if forced_rows:
        forced_frame = pd.DataFrame(forced_rows)
        trades = pd.concat([trades, forced_frame], ignore_index=True) if not trades.empty else forced_frame
    result["decisions"] = decisions
    result["paper_trades"] = trades
    return result


def _simulate_forced_entry(row: pd.Series, provider: ReplayDataProvider, clock: ReplayClock, config: ReplaySessionConfig) -> dict | None:
    market = str(row["market"])
    entry_at = _hhmm(config.date_kst, config.entry_time or config.decision_time)
    trade_end = _hhmm(config.date_kst, config.trade_end_time)
    clock.set(trade_end)
    outcome = provider.get_candles(market, "1s", 4500)
    fill_timeframe = "1s"
    if outcome.empty:
        outcome = provider.get_candles(market, "1m", 100)
        fill_timeframe = "1m"
    outcome = outcome[outcome["time"] >= pd.Timestamp(entry_at)]
    if outcome.empty:
        return None
    signal_price = float(outcome.iloc[0]["open"])
    stop_loss = signal_price * 0.985
    take_profit = signal_price * 1.015
    fill = simulate_long_trade(outcome, signal_price, stop_loss, take_profit)
    payload = {
        "session_id": row["session_id"],
        "date_kst": config.date_kst.isoformat(),
        "market": market,
        "decision_time_kst": _hhmm(config.date_kst, config.decision_time).isoformat(),
        "entry_time_kst": entry_at.isoformat(),
        "target_window_end_time_kst": _hhmm(config.date_kst, config.target_window_end_time).isoformat(),
        "trade_end_time_kst": trade_end.isoformat(),
        "strategy_label": config.strategy_label,
        "day_type": "weekend" if config.date_kst.weekday() >= 5 else "weekday",
        "fill_timeframe": fill_timeframe,
        "forced_entry": True,
        "force_entry_reason": "daily_best_candidate",
        "original_final_decision": row.get("final_decision", ""),
        "original_no_entry_reason": row.get("no_entry_reason", ""),
        "final_score": float(row.get("final_score", 0.0)),
    }
    payload.update(fill.__dict__)
    return payload

