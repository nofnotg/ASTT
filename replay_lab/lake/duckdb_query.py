from __future__ import annotations

from pathlib import Path


def query_parquet(sql: str, parquet_path: Path):
    import duckdb

    return duckdb.sql(sql.replace("$PARQUET", parquet_path.as_posix())).df()

