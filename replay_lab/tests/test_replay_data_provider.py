from datetime import datetime

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.replay_data_provider import ReplayDataProvider


def test_trade_proxy_uses_past_candles_only():
    frame = pd.DataFrame(
        [
            {"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": "2026-02-10T09:00:00", "open": 100, "high": 101, "low": 99, "close": 101, "volume": 3, "trade_price": 303},
            {"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": "2026-02-10T09:01:00", "open": 101, "high": 102, "low": 100, "close": 100, "volume": 2, "trade_price": 200},
        ]
    )
    provider = ReplayDataProvider(ReplayClock(datetime(2026, 2, 10, 9, 0)), {("KRW-BTC", "1m"): frame})
    trades = provider.get_trade_proxy("KRW-BTC", datetime(2026, 2, 10, 9, 0))
    assert len(trades) == 1
    assert trades.iloc[0]["ask_bid"] == "BID"

