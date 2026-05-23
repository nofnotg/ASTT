from datetime import datetime, timedelta

import pandas as pd

from live_data.second_candle_collector import collect_second_candles, fetch_second_candles, fill_missing_seconds


class _Client:
    def get_candles_seconds(self, market, count, to):
        return [{"market": market, "candle_date_time_kst": "2026-05-01T09:00:00", "opening_price": 100, "high_price": 101, "low_price": 99, "trade_price": 100.5, "candle_acc_trade_volume": 1.0}]


def test_fetch_second_candles_rejects_old_range():
    old_to = datetime.utcnow() - timedelta(days=120)

    assert fetch_second_candles("KRW-BTC", to=old_to, client=_Client()) == []


def test_fill_missing_seconds_marks_synthetic():
    frame = pd.DataFrame([{"time": "2026-05-01T09:00:00", "open": 100, "high": 100, "low": 100, "close": 100, "volume": 1, "market": "KRW-BTC"}])

    filled = fill_missing_seconds(frame, "2026-05-01T09:00:00", "2026-05-01T09:00:02")

    assert len(filled) == 3
    assert int(filled["synthetic"].sum()) == 2


def test_collect_second_candles_empty_response(monkeypatch, tmp_path):
    monkeypatch.setattr("live_data.second_candle_collector.fetch_second_candles", lambda *args, **kwargs: [])

    summary = collect_second_candles(["KRW-BTC"], days=1, store_dir=tmp_path)

    assert summary["actual_second_count"] == 0
    assert summary["data_quality"] == "UNAVAILABLE"
