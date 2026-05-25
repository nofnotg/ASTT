from __future__ import annotations

import pandas as pd

from btcd.btcd_csv_loader import load_btcd_csv


def test_btcd_csv_loader_normalizes_columns(tmp_path):
    path = tmp_path / "btc_dominance.csv"
    pd.DataFrame({"date": ["2024-01-01"], "dominance": [52.3], "source": ["unit"]}).to_csv(path, index=False)

    frame = load_btcd_csv(path)

    assert list(frame.columns) == ["timestamp", "btc_dominance_pct", "source"]
    assert float(frame.iloc[0]["btc_dominance_pct"]) == 52.3

