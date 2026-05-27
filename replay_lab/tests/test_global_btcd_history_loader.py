from __future__ import annotations

import pandas as pd

from btcd.global_btcd_history_loader import load_global_btcd_history


def test_global_btcd_history_loader_reports_missing_without_fake_data(tmp_path):
    frame, quality = load_global_btcd_history(tmp_path / "missing.csv")
    assert frame.empty
    assert quality["data_quality"] == "GLOBAL_BTCD_DATA_REQUIRED"
    assert "Fake history was not generated" in quality["notes"]


def test_global_btcd_history_loader_reads_csv(tmp_path):
    path = tmp_path / "btc_dominance_history.csv"
    pd.DataFrame({"timestamp": ["2022-01-01"], "btc_dominance_pct": [40.0], "source": ["csv"]}).to_csv(path, index=False)
    frame, quality = load_global_btcd_history(path)
    assert len(frame) == 1
    assert quality["available"] is True
