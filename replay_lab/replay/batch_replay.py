from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.feedback.replay_report import write_replay_report
from replay_lab.paths import REPLAY_STORE_DIR
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
    trade_end_time: str = "09:30",
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

