from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from replay_lab.feedback.replay_report import summarize_frames
from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store


class ExperimentRegistry:
    def __init__(self, db_path: Path | None = None) -> None:
        ensure_replay_store()
        self.db_path = db_path or REPLAY_STORE_DIR / "manifests" / "experiment_registry.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replay_experiments (
                    experiment_id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    markets_scope TEXT,
                    config_version TEXT,
                    status TEXT,
                    total_sessions INTEGER,
                    total_candidates INTEGER,
                    total_entries INTEGER,
                    win_rate REAL,
                    realized_pnl_pct REAL,
                    max_drawdown_pct REAL,
                    final_score_corr REAL,
                    maggie_signal_quality REAL,
                    rezo_signal_quality REAL,
                    iris_veto_effect REAL,
                    report_path TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )

    def upsert_completed(self, experiment_id: str, start_date: str, end_date: str, markets_scope: str, report_path: Path, frames: dict[str, pd.DataFrame]) -> None:
        metrics = summarize_frames(frames)
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO replay_experiments (
                    experiment_id, name, description, start_date, end_date, markets_scope, config_version,
                    status, total_sessions, total_candidates, total_entries, win_rate, realized_pnl_pct,
                    max_drawdown_pct, final_score_corr, maggie_signal_quality, rezo_signal_quality,
                    iris_veto_effect, report_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(experiment_id) DO UPDATE SET
                    status=excluded.status,
                    total_sessions=excluded.total_sessions,
                    total_candidates=excluded.total_candidates,
                    total_entries=excluded.total_entries,
                    win_rate=excluded.win_rate,
                    realized_pnl_pct=excluded.realized_pnl_pct,
                    report_path=excluded.report_path,
                    updated_at=excluded.updated_at
                """,
                (
                    experiment_id,
                    experiment_id,
                    "09:00 replay batch",
                    start_date,
                    end_date,
                    markets_scope,
                    "v0.1",
                    "COMPLETED",
                    metrics["sessions"],
                    metrics["decisions"],
                    metrics["entries"],
                    metrics["win_rate"],
                    metrics["total_pnl_pct"],
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    str(report_path),
                    now,
                    now,
                ),
            )

