from __future__ import annotations

from pathlib import Path

from btcd.btcdom_index_normalizer import normalize_btcdom_index_files


def test_btcdom_index_normalizer_writes_normalized_files(tmp_path: Path):
    external = tmp_path / "external"
    processed = tmp_path / "processed"
    external.mkdir()
    for tf in ("1h", "4h", "1d"):
        (external / f"btcdom_{tf}.csv").write_text(
            "timestamp,open,high,low,close,volume,datetime\n"
            "1685275200000,1,2,1,1612.9,10,2023-05-28 12:00:00\n",
            encoding="utf-8",
        )
    quality = normalize_btcdom_index_files(external, processed)
    assert quality["data_quality"] == "GOOD"
    assert quality["source_type"] == "BTCDOM_INDEX_PROXY"
    assert (processed / "btcdom_index_1h_normalized.csv").exists()
