from datetime import date, datetime, timedelta

import pandas as pd

from replay_lab.clock.replay_clock import ReplayClock
from replay_lab.data.replay_data_provider import ReplayDataProvider
from replay_lab.replay.replay_runner_0900 import ReplayRunner0900
from replay_lab.replay.replay_session import ReplaySessionConfig


def _fixture_frame(day: date) -> pd.DataFrame:
    start = datetime.combine(day, datetime.min.time()).replace(hour=8, minute=0)
    rows = []
    price = 1000.0
    for i in range(100):
        ts = start + timedelta(minutes=i)
        volume = 100 + i
        if ts.hour == 9 and ts.minute in {0, 1, 2, 3}:
            volume = 1000
        close = price * (1.001 if ts.hour == 9 else 1.0001)
        rows.append({"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": ts.isoformat(), "open": price, "high": close * 1.004, "low": price * 0.998, "close": close, "volume": volume, "trade_price": close * volume})
        price = close
    return pd.DataFrame(rows)


def test_single_day_replay_generates_decision_rows():
    day = date(2026, 2, 10)
    frame = _fixture_frame(day)
    clock = ReplayClock(datetime.combine(day, datetime.min.time()).replace(hour=8, minute=50))
    provider = ReplayDataProvider(clock, {("KRW-BTC", "1m"): frame})
    config = ReplaySessionConfig(session_id="test", date_kst=day, markets=["KRW-BTC"])
    result = ReplayRunner0900(provider, clock).run(config)
    assert len(result["decisions"]) == 1
    assert len(result["persona_scores"]) == 5
    assert result["decisions"].iloc[0]["market"] == "KRW-BTC"

