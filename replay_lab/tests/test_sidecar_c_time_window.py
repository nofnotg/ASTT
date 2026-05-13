from datetime import date, datetime, timedelta

import pandas as pd

from replay_lab.sidecar_c.time_window_discovery import TimeWindowDiscovery, TimeWindowDiscoveryConfig


def test_sidecar_c_builds_time_window_report(tmp_path):
    market_dir = tmp_path / "normalized" / "candles_1m"
    market_dir.mkdir(parents=True)
    day = date(2026, 1, 2)
    start = datetime.combine(day, datetime.min.time()).replace(hour=8, minute=0)
    rows = []
    price = 1000.0
    for index in range(150):
        ts = start + timedelta(minutes=index)
        close = price * (1.002 if ts.hour == 9 and ts.minute <= 30 else 1.0001)
        rows.append(
            {
                "market": "KRW-BTC",
                "timeframe": "1m",
                "candle_time_kst": ts.isoformat(),
                "open": price,
                "high": close * 1.002,
                "low": price * 0.999,
                "close": close,
                "volume": 10 + index,
                "trade_price": close * (10 + index),
            }
        )
        price = close
    pd.DataFrame(rows).to_parquet(market_dir / "KRW-BTC.parquet", index=False)

    out_dir = TimeWindowDiscovery(tmp_path).run(
        TimeWindowDiscoveryConfig(
            start_date=day,
            end_date=day,
            markets=["KRW-BTC"],
            entry_times=["09:00"],
        )
    )

    assert (out_dir / "time_window_discovery.html").exists()
    payload = pd.read_parquet(out_dir / "time_window_raw.parquet")
    assert len(payload) == 1
    assert payload.iloc[0]["entry_time"] == "09:00"
