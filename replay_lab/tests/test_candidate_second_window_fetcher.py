from data.candidate_second_window_fetcher import fetch_candidate_second_window


def test_candidate_second_window_fetcher_window_and_quality(monkeypatch, tmp_path):
    rows = [{"market": "KRW-BTC", "candle_date_time_kst": "2026-05-23T09:00:00", "opening_price": 100, "high_price": 101, "low_price": 99, "trade_price": 100, "candle_acc_trade_volume": 1, "candle_acc_trade_price": 100, "timestamp": 1}]
    monkeypatch.setattr("data.candidate_second_window_fetcher.get_second_candles", lambda *args, **kwargs: rows)
    monkeypatch.setattr("data.candidate_second_window_fetcher.store_candidate_second_window", lambda window: {"json_path": "x", "parquet_path": "y"})

    result = fetch_candidate_second_window("KRW-BTC", "2026-05-23T09:00:00", pre_seconds=2, post_seconds=2)

    assert result["actual_second_count"] == 1
    assert result["synthetic_second_count"] == 4
    assert result["data_source"] == "UPBIT_REST_SECONDS"
