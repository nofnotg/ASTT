from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from atr_ltf.ltf_data_schema import LTFBar


def load_ltf_bars(path: str | Path, market: str, timeframe: str) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []
    if source.suffix.lower() == ".csv":
        return _load_csv(source, market, timeframe)
    if source.suffix.lower() == ".jsonl":
        return [_normalize(json.loads(line), market, timeframe) for line in source.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if source.suffix.lower() == ".json":
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        rows = payload if isinstance(payload, list) else payload.get("rows", [])
        return [_normalize(row, market, timeframe) for row in rows]
    return []


def bars_between(rows: list[dict[str, Any]], start_time: str, end_time: str) -> list[dict[str, Any]]:
    start = str(start_time)
    end = str(end_time)
    return [row for row in rows if start <= str(row.get("timestamp", "")) <= end]


def _load_csv(path: Path, market: str, timeframe: str) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [_normalize(row, market, timeframe) for row in csv.DictReader(handle)]


def _normalize(row: dict[str, Any], market: str, timeframe: str) -> dict[str, Any]:
    ts = row.get("timestamp") or row.get("time") or row.get("datetime") or row.get("candle_date_time_utc") or row.get("date")
    bar = LTFBar(
        market=str(row.get("market") or market),
        timestamp=str(ts or ""),
        open=_num(row.get("open") or row.get("opening_price")),
        high=_num(row.get("high") or row.get("high_price")),
        low=_num(row.get("low") or row.get("low_price")),
        close=_num(row.get("close") or row.get("trade_price")),
        volume=_num(row.get("volume") or row.get("candle_acc_trade_volume")),
        timeframe=timeframe,
    )
    return bar.as_dict()


def _num(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
