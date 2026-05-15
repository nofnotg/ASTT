from datetime import date, datetime, timedelta

import pandas as pd

from replay_lab.research.time_window_sweep_v3 import default_windows, evaluate_time_windows


def _frame(day: date) -> pd.DataFrame:
    start = datetime.combine(day, datetime.min.time())
    rows = []
    price = 1000.0
    for idx in range(24 * 60):
        ts = start + timedelta(minutes=idx)
        close = price * (1.0005 if ts.hour == 9 else 1.00005)
        rows.append({"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": ts, "open": price, "high": close * 1.002, "low": price * 0.998, "close": close, "volume": 1000 + idx, "trade_price": close * (1000 + idx)})
        price = close
    return pd.DataFrame(rows)


def test_default_windows_can_generate_30_minute_grid():
    windows = default_windows(30)
    assert "09:00" in windows
    assert "23:30" not in windows


def test_time_window_sweep_ranks_by_risk_adjusted_score(tmp_path):
    root = tmp_path / "normalized" / "candles_1m"
    root.mkdir(parents=True)
    _frame(date(2026, 1, 1)).to_parquet(root / "KRW-BTC.parquet", index=False)
    rows, trades = evaluate_time_windows(date(2026, 1, 1), date(2026, 1, 1), ["KRW-BTC"], ["09:00", "10:00"], store_dir=tmp_path)
    assert len(rows) == 2
    assert rows == sorted(rows, key=lambda row: row["risk_adjusted_score"], reverse=True)
    assert not trades.empty
