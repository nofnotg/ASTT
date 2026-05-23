import pandas as pd

from replay_lab.replay.second_candle_replay import replay_second_candles


def test_second_candle_replay_fills_missing_seconds(tmp_path):
    root = tmp_path / "normalized" / "upbit_seconds" / "KRW-BTC"
    root.mkdir(parents=True)
    pd.DataFrame([
        {"market": "KRW-BTC", "candle_time_kst": "2026-05-01T09:00:00", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1},
        {"market": "KRW-BTC", "candle_time_kst": "2026-05-01T09:00:02", "open": 101, "high": 101, "low": 101, "close": 101, "volume": 1},
    ]).to_parquet(root / "2026-05-01.parquet", index=False)

    result = replay_second_candles("KRW-BTC", "2026-05-01T09:00:00", "2026-05-01T09:00:02", store_dir=tmp_path)

    assert result["actual_second_count"] == 2
    assert result["synthetic_second_count"] == 1
    assert result["data_quality"] == "PARTIAL"


def test_second_candle_replay_unavailable_when_no_data(tmp_path):
    result = replay_second_candles("KRW-BTC", "2026-05-01T09:00:00", "2026-05-01T09:00:02", store_dir=tmp_path)

    assert result["data_quality"] == "UNAVAILABLE"
