from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_BTCD_CACHE = Path("data/external/btc_dominance_cache.sqlite")


def ensure_btcd_storage(db_path: str | Path = DEFAULT_BTCD_CACHE) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS btc_dominance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                dominance REAL,
                market_cap_usd REAL,
                volume_24h_usd REAL,
                fetched_at TEXT NOT NULL,
                source_updated_at TEXT
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_btc_dominance_source ON btc_dominance(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_btc_dominance_fetched_at ON btc_dominance(fetched_at)")
    return path


def save_btcd_record(record: dict[str, Any], db_path: str | Path = DEFAULT_BTCD_CACHE) -> dict[str, Any]:
    path = ensure_btcd_storage(db_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO btc_dominance(source, dominance, market_cap_usd, volume_24h_usd, fetched_at, source_updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("source"),
                record.get("dominance"),
                record.get("market_cap_usd"),
                record.get("volume_24h_usd"),
                record.get("fetched_at"),
                record.get("source_updated_at"),
            ),
        )
    return {"db_path": str(path), "saved": True, "source": record.get("source")}


def latest_btcd_record(source: str = "coinpaprika", db_path: str | Path = DEFAULT_BTCD_CACHE) -> dict[str, Any] | None:
    path = ensure_btcd_storage(db_path)
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            """
            SELECT source, dominance, market_cap_usd, volume_24h_usd, fetched_at, source_updated_at
            FROM btc_dominance WHERE source = ? ORDER BY fetched_at DESC LIMIT 1
            """,
            (source,),
        ).fetchone()
    if not row:
        return None
    return {
        "source": row[0],
        "dominance": row[1],
        "market_cap_usd": row[2],
        "volume_24h_usd": row[3],
        "fetched_at": row[4],
        "source_updated_at": row[5],
    }
