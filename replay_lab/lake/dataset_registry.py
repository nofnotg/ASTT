from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from replay_lab.paths import REPLAY_STORE_DIR, ensure_replay_store


@dataclass(frozen=True)
class DatasetRecord:
    dataset_id: str
    exchange: str
    market: str
    data_type: str
    timeframe: str
    start_time_kst: str
    end_time_kst: str
    row_count: int
    source: str
    storage_path: str
    quality_score: float
    missing_count: int


class DatasetRegistry:
    def __init__(self, db_path: Path | None = None) -> None:
        ensure_replay_store()
        self.db_path = db_path or REPLAY_STORE_DIR / "manifests" / "dataset_manifest.sqlite"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replay_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT UNIQUE NOT NULL,
                    exchange TEXT NOT NULL,
                    market TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    start_time_kst TEXT NOT NULL,
                    end_time_kst TEXT NOT NULL,
                    row_count INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    storage_path TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    missing_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def upsert(self, record: DatasetRecord) -> None:
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO replay_datasets (
                    dataset_id, exchange, market, data_type, timeframe,
                    start_time_kst, end_time_kst, row_count, source, storage_path,
                    quality_score, missing_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dataset_id) DO UPDATE SET
                    start_time_kst=excluded.start_time_kst,
                    end_time_kst=excluded.end_time_kst,
                    row_count=excluded.row_count,
                    storage_path=excluded.storage_path,
                    quality_score=excluded.quality_score,
                    missing_count=excluded.missing_count,
                    updated_at=excluded.updated_at
                """,
                (
                    record.dataset_id,
                    record.exchange,
                    record.market,
                    record.data_type,
                    record.timeframe,
                    record.start_time_kst,
                    record.end_time_kst,
                    record.row_count,
                    record.source,
                    record.storage_path,
                    record.quality_score,
                    record.missing_count,
                    now,
                    now,
                ),
            )

    def find_covering(self, market: str, data_type: str, timeframe: str, start: str, end: str) -> DatasetRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT dataset_id, exchange, market, data_type, timeframe, start_time_kst,
                       end_time_kst, row_count, source, storage_path, quality_score, missing_count
                FROM replay_datasets
                WHERE market=? AND data_type=? AND timeframe=?
                  AND start_time_kst<=? AND end_time_kst>=?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (market, data_type, timeframe, start, end),
            ).fetchone()
        return DatasetRecord(*row) if row else None

    def list_all(self) -> list[DatasetRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT dataset_id, exchange, market, data_type, timeframe, start_time_kst,
                       end_time_kst, row_count, source, storage_path, quality_score, missing_count
                FROM replay_datasets
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [DatasetRecord(*row) for row in rows]

