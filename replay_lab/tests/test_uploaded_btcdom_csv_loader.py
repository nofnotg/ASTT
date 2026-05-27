from __future__ import annotations

from pathlib import Path

from btcd.uploaded_btcdom_csv_loader import classify_btcdom_source_type, load_uploaded_btcdom_csv


def test_uploaded_btcdom_loader_handles_binance_like_csv(tmp_path: Path):
    path = tmp_path / "btcdom_1h.csv"
    path.write_text(
        "timestamp,open,high,low,close,volume,datetime\n"
        "1685275200000,1,2,1,1612.9,10,2023-05-28 12:00:00\n",
        encoding="utf-8",
    )
    frame, summary = load_uploaded_btcdom_csv(path)
    assert len(frame) == 1
    assert summary["source_type"] == "BTCDOM_INDEX_PROXY"
    assert summary["is_percentage"] is False


def test_classify_btcdom_percentage_vs_index_proxy():
    source_type, is_pct = classify_btcdom_source_type([50, 51, 52])
    assert source_type == "GLOBAL_BTCD_PERCENTAGE"
    assert is_pct is True
    source_type, is_pct = classify_btcdom_source_type([1600, 1700, 1800])
    assert source_type == "BTCDOM_INDEX_PROXY"
    assert is_pct is False


def test_uploaded_btcdom_loader_treats_percent_style_index_as_proxy(tmp_path: Path):
    path = tmp_path / "btcdom_1d_percent.csv"
    path.write_text(
        "timestamp_ms,datetime_utc,open_pct,high_pct,low_pct,close_pct,volume,source_note\n"
        "1685318400000,2023-05-29 00:00:00,16.1,16.2,16.0,16.119,10,Binance BTCDOM index raw value divided by 100 for percent-style display; not CMC/TradingView market-cap BTC.D.\n",
        encoding="utf-8",
    )
    frame, summary = load_uploaded_btcdom_csv(path)
    assert frame.iloc[0]["close"] == 16.119
    assert summary["source_type"] == "BTCDOM_INDEX_PROXY"
    assert summary["is_percentage"] is False
