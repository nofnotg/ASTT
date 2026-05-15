from datetime import date, datetime, timedelta

import pandas as pd

from replay_lab.research.preopen_confirmed_compare import choose_better_mode, evaluate_entry_mode


def _frame(day: date) -> pd.DataFrame:
    start = datetime.combine(day, datetime.min.time())
    rows = []
    price = 1000.0
    for idx in range(11 * 60):
        ts = start + timedelta(minutes=idx)
        close = price * (1.001 if ts.hour == 9 and ts.minute < 20 else 1.0001)
        rows.append({"market": "KRW-BTC", "timeframe": "1m", "candle_time_kst": ts, "open": price, "high": close * 1.004, "low": price * 0.998, "close": close, "volume": 1500 + idx, "trade_price": close * (1500 + idx)})
        price = close
    return pd.DataFrame(rows)


def test_preopen_and_confirmed_are_evaluated_separately(tmp_path):
    root = tmp_path / "normalized" / "candles_1m"
    root.mkdir(parents=True)
    _frame(date(2026, 1, 1)).to_parquet(root / "KRW-BTC.parquet", index=False)

    preopen = evaluate_entry_mode("preopen", date(2026, 1, 1), date(2026, 1, 1), ["KRW-BTC"], store_dir=tmp_path)
    confirmed = evaluate_entry_mode("confirmed", date(2026, 1, 1), date(2026, 1, 1), ["KRW-BTC"], store_dir=tmp_path)

    assert preopen["summary"]["mode"] == "preopen"
    assert confirmed["summary"]["mode"] == "confirmed"
    assert choose_better_mode(preopen["summary"], confirmed["summary"]) in {"preopen", "confirmed"}
