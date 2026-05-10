from datetime import datetime, timedelta

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.replay_data_provider import ReplayDataProvider


def test_provider_returns_only_clock_visible_candles():
    base = datetime(2026, 2, 10, 9, 0)
    frame = pd.DataFrame(
        [
            {"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": (base + timedelta(minutes=i)).isoformat(), "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "trade_price": 1}
            for i in range(5)
        ]
    )
    clock = ReplayClock(datetime(2026, 2, 10, 9, 3))
    provider = ReplayDataProvider(clock, {("KRW-BTC", "1m"): frame})
    candles = provider.get_candles("KRW-BTC", "1m", 10)
    assert len(candles) == 4
    assert candles["time"].max() == pd.Timestamp(datetime(2026, 2, 10, 9, 3))

