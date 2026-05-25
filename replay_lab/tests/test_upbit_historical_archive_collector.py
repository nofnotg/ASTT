from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from market_data.upbit_historical_archive_collector import collect_upbit_historical_archive


class FakeHistoricalLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def load_top_krw_markets(self, limit: int) -> list[str]:
        return ["KRW-AAA"][:limit]

    def load_candles(self, market: str, timeframe: str, start: datetime, end: datetime) -> Path:
        times = [end - timedelta(days=2), end - timedelta(days=1), end]
        frame = pd.DataFrame(
            {
                "time": times,
                "open": [100.0, 101.0, 102.0],
                "high": [103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0],
                "close": [102.0, 103.0, 104.0],
                "volume": [10.0, 11.0, 12.0],
            }
        )
        path = self.root / f"{market}_{timeframe}.parquet"
        frame.to_parquet(path, index=False)
        return path


def test_collect_upbit_historical_archive_records_actual_coverage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = collect_upbit_historical_archive(
        markets="TOP_KRW_1",
        timeframes="1d",
        max_lookback_days=10,
        archive_dir=tmp_path / "archive",
        loader=FakeHistoricalLoader(tmp_path),
    )

    assert result["real_order_enabled"] is False
    assert result["live_order_allowed"] is False
    assert result["rows"][0]["candles"] == 3
    assert result["rows"][0]["earliest_available_time"] is not None
    assert (tmp_path / "archive/1d/KRW-AAA.parquet").exists()
    assert (tmp_path / "archive/1w/KRW-AAA.parquet").exists()
    assert (tmp_path / "docs/reports/latest_historical_archive_summary.json").exists()
