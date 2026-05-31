from __future__ import annotations

from pathlib import Path
from typing import Any

from atr_ltf.ltf_data_schema import TIMEFRAMES


DEFAULT_SEARCH_ROOTS = (
    "data/ltf",
    "data/external",
    "data/processed",
    "replay_store/v6_ohlcv",
    "replay_store/historical_archive",
)


def find_ltf_files(market: str, timeframe: str, search_roots: list[str | Path] | None = None) -> list[Path]:
    if timeframe not in TIMEFRAMES:
        return []
    roots = [Path(root) for root in (search_roots or DEFAULT_SEARCH_ROOTS)]
    market_tokens = _market_tokens(market)
    matches: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".json", ".jsonl"}:
                continue
            name = path.name.lower()
            if timeframe.lower() not in name:
                continue
            if any(token in name for token in market_tokens):
                matches.append(path)
    return sorted(matches)


def coverage_source_status(market: str, search_roots: list[str | Path] | None = None) -> dict[str, Any]:
    return {timeframe: [str(path) for path in find_ltf_files(market, timeframe, search_roots)] for timeframe in TIMEFRAMES}


def _market_tokens(market: str) -> list[str]:
    raw = market.lower()
    compact = raw.replace("-", "").replace("_", "")
    parts = [part for part in raw.replace("_", "-").split("-") if part]
    return sorted(set([raw, compact, *parts]), key=len, reverse=True)
